import React, { useState, useEffect, useRef, useCallback } from "react";
import SinglePostCard from "../components/SinglePost";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';

const LIMIT = 10;

function Feed({ currentUser }) {
  const [tab, setTab] = useState('global');      // 'global' | 'following'
  const [posts, setPosts] = useState([]);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const requestId = useRef(0);

  // Load the global feed page-by-page (lazy loading via limit/offset).
  const loadGlobal = async (currentOffset) => {
    const myId = ++requestId.current;
    setIsLoading(true);
    const res = await fetch(`/api/feed?limit=${LIMIT}&offset=${currentOffset}`, { credentials: 'include' });
    const data = await res.json();
    if (myId !== requestId.current) return; // a newer request superseded this one
    setPosts(prev => currentOffset === 0 ? data : [...prev, ...data]);
    setHasMore(data.length === LIMIT);
    setIsLoading(false);
  };

  // Load the individual feed (posts from people the user follows).
  const loadFollowing = async () => {
    const myId = ++requestId.current;
    setIsLoading(true);
    const res = await fetch('/api/feed/following', { credentials: 'include' });
    const data = res.ok ? await res.json() : [];
    if (myId !== requestId.current) return;
    setPosts(Array.isArray(data) ? data : []);
    setHasMore(false); // following feed is returned in one shot
    setIsLoading(false);
  };

  useEffect(() => {
    setPosts([]);
    setOffset(0);
    if (tab === 'global') {
      loadGlobal(0);
    } else {
      loadFollowing();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const loadMore = () => {
    const newOffset = offset + LIMIT;
    setOffset(newOffset);
    loadGlobal(newOffset);
  };

  // ── Infinite scroll ──────────────────────────────────────────────────────
  // Watch a sentinel element at the bottom of the list. When it scrolls into
  // view (and there's more to load), fetch the next page automatically.
  const observer = useRef(null);
  const sentinelRef = useCallback((node) => {
    if (observer.current) observer.current.disconnect();
    if (!node) return;

    observer.current = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && tab === 'global' && hasMore && !isLoading) {
        loadMore();
      }
    }, { rootMargin: '200px' }); // start loading a little before the very bottom

    observer.current.observe(node);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, hasMore, isLoading, offset]);

  return (
    <Box sx={{ mt: 12 }}>
      <Tabs value={tab} onChange={(e, v) => setTab(v)} centered sx={{ mb: 3 }}>
        <Tab label="Global Feed" value="global" />
        <Tab label="Following" value="following" disabled={!currentUser} />
      </Tabs>

      {tab === 'following' && !currentUser && (
        <Typography sx={{ textAlign: 'center', color: 'text.secondary' }}>
          Log in to see posts from people you follow.
        </Typography>
      )}

      {!isLoading && posts.length === 0 && tab === 'following' && currentUser && (
        <Typography sx={{ textAlign: 'center', color: 'text.secondary' }}>
          No posts yet — follow some users to fill your feed!
        </Typography>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        {posts.map((post) => (
          <SinglePostCard
            key={post.id}
            title={post.title}
            authorName={post.author_name}
            authorEmail={post.author_email}
            body={post.body}
            imageUrl={post.image_url}
            createdAt={post.created_at}
            profilePictureUrl={post.profile_picture_url}
          />
        ))}
      </div>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Invisible sentinel: when it scrolls into view, the next page loads. */}
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
