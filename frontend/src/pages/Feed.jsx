import { useState, useEffect, useRef, useCallback } from 'react';
import { Box, Tabs, Tab, Typography, CircularProgress } from '@mui/material';
import SinglePostCard from '../components/SinglePost';
import { fetchGlobalFeed, fetchFollowingFeed } from '../api';

const PAGE_SIZE = 10;

/**
 * The blog home page. Two tabs:
 *  - "Latest": every post, newest first, loaded page-by-page with
 *    infinite scroll (a sentinel div at the bottom triggers the next page).
 *  - "Following": posts only from authors the logged-in user follows,
 *    returned by the backend in one shot.
 */
function Feed({ currentUser }) {
  const [tab, setTab] = useState('global'); // 'global' | 'following'
  const [posts, setPosts] = useState([]);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);

  // Each fetch gets an increasing id; a response is ignored if a newer
  // request started after it (e.g. the user switched tabs mid-load).
  const requestId = useRef(0);

  // The loaders only fetch and store results; callers set isLoading first.
  const loadGlobal = async (currentOffset) => {
    const myId = ++requestId.current;
    const data = await fetchGlobalFeed(PAGE_SIZE, currentOffset);
    if (myId !== requestId.current) return; // superseded by a newer request
    setPosts(prev => (currentOffset === 0 ? data : [...prev, ...data]));
    setHasMore(data.length === PAGE_SIZE); // a short page means we reached the end
    setIsLoading(false);
  };

  const loadFollowing = async () => {
    const myId = ++requestId.current;
    const data = await fetchFollowingFeed().catch(() => []);
    if (myId !== requestId.current) return;
    setPosts(Array.isArray(data) ? data : []);
    setHasMore(false); // following feed is not paginated
    setIsLoading(false);
  };

  // Load the first page when the page opens (isLoading starts as true)
  useEffect(() => {
    loadGlobal(0);
  }, []);

  // Switching tabs clears the list and reloads it from the new source
  const handleTabChange = (event, value) => {
    setTab(value);
    setPosts([]);
    setOffset(0);
    setIsLoading(true);
    if (value === 'global') {
      loadGlobal(0);
    } else {
      loadFollowing();
    }
  };

  const loadMore = () => {
    const newOffset = offset + PAGE_SIZE;
    setOffset(newOffset);
    setIsLoading(true);
    loadGlobal(newOffset);
  };

  // ── Infinite scroll ────────────────────────────────────────────────────
  // Watch an invisible sentinel element under the post grid. When it
  // scrolls into view (and there's more to load), fetch the next page.
  const observer = useRef(null);
  const sentinelRef = useCallback((node) => {
    if (observer.current) observer.current.disconnect();
    if (!node) return;

    observer.current = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && tab === 'global' && hasMore && !isLoading) {
        loadMore();
      }
    }, { rootMargin: '200px' }); // start loading a little before the bottom

    observer.current.observe(node);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, hasMore, isLoading, offset]);

  return (
    <Box sx={{ mt: 5 }}>
      {/* Page header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" sx={{ mb: 1 }}>
          Stories &amp; Ideas
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Read, write and share what matters to you.
        </Typography>
      </Box>

      <Tabs
        value={tab}
        onChange={handleTabChange}
        centered
        sx={{ mb: 4, borderBottom: '1px solid', borderColor: 'divider' }}
      >
        <Tab label="Latest" value="global" />
        <Tab label="Following" value="following" disabled={!currentUser} />
      </Tabs>

      {/* Empty states for the Following tab */}
      {tab === 'following' && !currentUser && (
        <Typography sx={{ textAlign: 'center', color: 'text.secondary' }}>
          Log in to see posts from people you follow.
        </Typography>
      )}
      {!isLoading && posts.length === 0 && tab === 'following' && currentUser && (
        <Typography sx={{ textAlign: 'center', color: 'text.secondary' }}>
          No posts yet — follow some authors to fill your feed!
        </Typography>
      )}

      {/* Post grid styled for larger, square tiles (Instagram-like) */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: '1fr', md: '1fr', lg: '1fr' },
          gap: 3,
          px: { xs: 1, md: 2 },
        }}
      >
        {posts.map((post) => (
          <SinglePostCard
            key={post.id}
            postId={post.id}
            title={post.title}
            authorName={post.author_name}
            authorEmail={post.author_email}
            body={post.body}
            imageUrl={post.image_url}
            createdAt={post.created_at}
            profilePictureUrl={post.profile_picture_url}
          />
        ))}
      </Box>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Invisible sentinel: when it scrolls into view, the next page loads */}
      {tab === 'global' && hasMore && !isLoading && (
        <Box ref={sentinelRef} sx={{ height: 1 }} />
      )}

      {!hasMore && posts.length > 0 && tab === 'global' && (
        <Typography sx={{ textAlign: 'center', color: 'text.secondary', mt: 4 }}>
          You're all caught up 🎉
        </Typography>
      )}
    </Box>
  );
}

export default Feed;
