import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getUserProfile, followUser, unfollowUser } from '../api';
import { timeAgo } from '../utils/timeAgo';

const UserPostsPage = ({ currentUser }) => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    getUserProfile(userId).then(data => setProfile(data));
  }, [userId]);

  const handleFollowToggle = async () => {
    if (!currentUser) {
      alert("You must be logged in to follow users!");
      return;
    }
    if (profile.is_following) {
      await unfollowUser(userId);
      setProfile({ ...profile, is_following: false, followers_count: profile.followers_count - 1 });
    } else {
      await followUser(userId);
      setProfile({ ...profile, is_following: true, followers_count: profile.followers_count + 1 });
    }
  };

  if (!profile) return <div>Loading...</div>;

  return (
    <div style={{ maxWidth: 700, margin: '80px auto 0', padding: '0 16px' }}>
      <button onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>← Back</button>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
        <img src={profile.profile_picture_url} alt="Profile" style={{ width: 80, height: 80, borderRadius: '50%', objectFit: 'cover' }} />
        <div>
          <h2 style={{ margin: 0 }}>{profile.name}</h2>
          <p style={{ margin: '4px 0', color: '#666' }}>{profile.bio}</p>
          <span>Followers: {profile.followers_count}</span> &nbsp;|&nbsp;
          <span>Following: {profile.following_count}</span>
        </div>
      </div>

      <button
        onClick={handleFollowToggle}
        disabled={!currentUser}
        title={!currentUser ? "Log in to follow users" : ""}
        style={{ marginBottom: 24 }}
      >
        {!currentUser ? 'Log in to follow' : profile.is_following ? 'Unfollow' : 'Follow'}
      </button>

      {profile.posts.map(post => (
        <div key={post.id} style={{ borderBottom: '1px solid #eee', paddingBottom: 12, marginBottom: 12 }}>
          <h3 style={{ margin: '0 0 4px' }}>{post.title}</h3>
          {post.image_url && (
            <img src={post.image_url} alt={post.title} style={{ maxWidth: '100%', borderRadius: 8, marginBottom: 8 }} />
          )}
          <div style={{ margin: '0 0 4px' }} dangerouslySetInnerHTML={{ __html: post.body || '' }} />
          <small style={{ color: '#999' }}>{timeAgo(post.created_at)}</small>
        </div>
      ))}
    </div>
  );
};

export default UserPostsPage;
