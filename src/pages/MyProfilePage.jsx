import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMe, getUserProfile, updateMyBio, getFollowers, getFollowing } from '../api';
import { timeAgo } from '../utils/timeAgo';
import {
  Box, Avatar, Typography, TextField, Button, CircularProgress, Card, CardContent, Divider,
  Dialog, DialogTitle, List, ListItem, ListItemButton, ListItemAvatar, ListItemText,
} from '@mui/material';

function MyProfilePage({ currentUser }) {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [bioDraft, setBioDraft] = useState('');
  const [saving, setSaving] = useState(false);

  // Followers / following dialog state
  const [dialog, setDialog] = useState(null);   // 'followers' | 'following' | null
  const [listUsers, setListUsers] = useState([]);
  const [listLoading, setListLoading] = useState(false);

  const openList = async (type) => {
    setDialog(type);
    setListLoading(true);
    setListUsers([]);
    try {
      const me = await getMe();
      const data = type === 'followers' ? await getFollowers(me.id) : await getFollowing(me.id);
      setListUsers(data);
    } catch {
      setListUsers([]);
    }
    setListLoading(false);
  };

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!currentUser) {
      navigate('/Login');
      return;
    }
    async function load() {
      try {
        const me = await getMe();              // get our own id from the session
        const data = await getUserProfile(me.id);
        setProfile(data);
        setBioDraft(data.bio || '');
      } catch {
        navigate('/Login');
      }
    }
    load();
  }, [currentUser]);

  const handleSaveBio = async () => {
    setSaving(true);
    try {
      await updateMyBio(bioDraft);
      setProfile({ ...profile, bio: bioDraft });
      setEditing(false);
    } catch {
      alert('Could not save bio. Please try again.');
    }
    setSaving(false);
  };

  if (!profile) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 12 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 700, mx: 'auto', mt: 12 }}>
      {/* ── Profile header ── */}
      <Card sx={{ borderRadius: 3, boxShadow: 2, mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <Avatar src={profile.profile_picture_url} alt={profile.name} sx={{ width: 96, height: 96 }} />
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h5" sx={{ fontWeight: 700 }}>{profile.name}</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>{profile.email}</Typography>
              <Box sx={{ mt: 1 }}>
                <Typography
                  component="span"
                  onClick={() => openList('followers')}
                  sx={{ mr: 2, cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}
                >
                  <strong>{profile.followers_count}</strong> followers
                </Typography>
                <Typography
                  component="span"
                  onClick={() => openList('following')}
                  sx={{ cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}
                >
                  <strong>{profile.following_count}</strong> following
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* ── Editable bio ── */}
          <Divider sx={{ my: 2 }} />
          {editing ? (
            <Box>
              <TextField
                fullWidth
                multiline
                minRows={2}
                value={bioDraft}
                onChange={e => setBioDraft(e.target.value)}
                label="Your bio"
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                onClick={handleSaveBio}
                disabled={saving}
                sx={{ background: '#5b6dfa', mr: 1 }}
              >
                {saving ? 'Saving...' : 'Save'}
              </Button>
              <Button
                variant="text"
                onClick={() => { setBioDraft(profile.bio || ''); setEditing(false); }}
                disabled={saving}
              >
                Cancel
              </Button>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
              <Typography sx={{ color: profile.bio ? 'text.primary' : 'text.secondary' }}>
                {profile.bio || 'No bio yet. Tell people about yourself!'}
              </Typography>
              <Button size="small" onClick={() => setEditing(true)}>Edit Bio</Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* ── My posts ── */}
      <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>My Posts</Typography>
      {profile.posts.length === 0 ? (
        <Typography sx={{ color: 'text.secondary' }}>You haven't posted anything yet.</Typography>
      ) : (
        profile.posts.map(post => (
          <Card key={post.id} sx={{ borderRadius: 2, boxShadow: 1, mb: 2 }}>
            {post.image_url && (
              <Box component="img" src={post.image_url} alt={post.title}
                sx={{ width: '100%', maxHeight: 240, objectFit: 'cover' }} />
            )}
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{post.title}</Typography>
              <Box sx={{ my: 0.5, '& a': { color: '#5b6dfa' } }}
                dangerouslySetInnerHTML={{ __html: post.body || '' }} />
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                {timeAgo(post.created_at)}
              </Typography>
            </CardContent>
          </Card>
        ))
      )}

      {/* ── Followers / Following dialog ── */}
      <Dialog open={dialog !== null} onClose={() => setDialog(null)} fullWidth maxWidth="xs">
        <DialogTitle sx={{ textTransform: 'capitalize' }}>{dialog}</DialogTitle>
        {listLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : listUsers.length === 0 ? (
          <Typography sx={{ p: 3, color: 'text.secondary' }}>
            {dialog === 'followers' ? 'No followers yet.' : 'Not following anyone yet.'}
          </Typography>
        ) : (
          <List sx={{ pt: 0 }}>
            {listUsers.map(u => (
              <ListItem key={u.id} disablePadding>
                <ListItemButton onClick={() => { setDialog(null); navigate(`/user-posts/${u.id}`); }}>
                  <ListItemAvatar>
                    <Avatar src={u.profile_picture_url} alt={u.name} />
                  </ListItemAvatar>
                  <ListItemText primary={u.name} secondary={u.email} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Dialog>
    </Box>
  );
}

export default MyProfilePage;
