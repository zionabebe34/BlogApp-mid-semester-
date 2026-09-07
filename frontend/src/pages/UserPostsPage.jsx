import { useEffect, useState } from 'react';
import DOMPurify from 'dompurify';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Typography, Button, Card, CardContent, Avatar, CircularProgress,
} from '@mui/material';
import { getUserProfile, followUser, unfollowUser } from '../api';
import { timeAgo } from '../utils/timeAgo';

/**
 * Public author page: profile header (avatar, bio, follower counts),
 * a follow/unfollow button, and every post the author has written.
 */
const UserPostsPage = ({ currentUser }) => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    getUserProfile(userId).then(setProfile);
  }, [userId]);

  // Flip the follow state and adjust the follower count locally,
  // so the UI updates without refetching the whole profile.
  const handleFollowToggle = async () => {
    try {
      if (profile.is_following) {
        await unfollowUser(userId);
        setProfile({ ...profile, is_following: false, followers_count: profile.followers_count - 1 });
      } else {
        await followUser(userId);
        setProfile({ ...profile, is_following: true, followers_count: profile.followers_count + 1 });
      }
    } catch (err) {
      alert(err.message);
    }
  };

  if (!profile) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 12 }}>
        <CircularProgress />
      </Box>
    );
  }

  const isOwnProfile = currentUser && String(currentUser.id) === String(userId);

  return (
    <Box sx={{ maxWidth: 700, mx: 'auto', mt: 4 }}>
      <Button onClick={() => navigate(-1)} sx={{ mb: 2, color: 'text.secondary' }}>
        ← Back
      </Button>

      {/* Author header */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <Avatar
              src={profile.profile_picture_url}
              alt={profile.name}
              sx={{ width: 88, height: 88 }}
            />
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h5">{profile.name}</Typography>
              {profile.bio && (
                <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
                  {profile.bio}
                </Typography>
              )}
              <Typography variant="body2" sx={{ mt: 1 }}>
                <strong>{profile.followers_count}</strong> followers ·{' '}
                <strong>{profile.following_count}</strong> following
              </Typography>
            </Box>

            {/* No follow button on your own profile */}
            {!isOwnProfile && (
              <Button
                variant={profile.is_following ? 'outlined' : 'contained'}
                onClick={handleFollowToggle}
                disabled={!currentUser}
                title={!currentUser ? 'Log in to follow authors' : ''}
              >
                {!currentUser ? 'Log in to follow' : profile.is_following ? 'Unfollow' : 'Follow'}
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Author's posts */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Posts by {profile.name}
      </Typography>
      {profile.posts.length === 0 ? (
        <Typography sx={{ color: 'text.secondary' }}>No posts yet.</Typography>
      ) : (
        profile.posts.map(post => (
          <Card key={post.id} sx={{ mb: 2 }}>
            {post.image_url && (
              <Box
                component="img"
                src={post.image_url}
                alt={post.title}
                sx={{ width: '100%', maxHeight: 260, objectFit: 'cover', display: 'block' }}
              />
            )}
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1 }}>{post.title}</Typography>
              <Box
                className="post-body"
                sx={{ color: 'text.secondary', mb: 1 }}
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(post.body || '') }}
              />
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                {timeAgo(post.created_at)}
              </Typography>
            </CardContent>
          </Card>
        ))
      )}
    </Box>
  );
};

export default UserPostsPage;
