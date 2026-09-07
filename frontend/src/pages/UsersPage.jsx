import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, TextField, Button, CircularProgress,
  Card, CardContent, Avatar,
} from '@mui/material';
import { fetchUsersWithPostCounts, searchUsers } from '../api';

/**
 * "Authors" page: every user with their post count, searchable by name
 * or email. Typing in the search box is debounced (we wait 400ms after
 * the last keystroke before asking the backend) and results are shown
 * a few at a time with a "Load More" button.
 */
function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [visibleCount, setVisibleCount] = useState(5);
  const navigate = useNavigate();
  const debounceTimer = useRef(null);

  // Fetch everyone once on page load
  useEffect(() => {
    fetchUsersWithPostCounts()
      .then(setUsers)
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  }, []);

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearch(value);
    setVisibleCount(5);

    // Debounce: restart the 400ms timer on every keystroke
    clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(async () => {
      setLoading(true);
      try {
        const results = value.trim() === ''
          ? await fetchUsersWithPostCounts()          // empty box → show everyone
          : await searchUsers(value);                 // otherwise → backend search
        setUsers(results.map(u => ({ ...u, postCount: u.postCount ?? 0 })));
      } catch {
        setUsers([]);
      }
      setLoading(false);
    }, 400);
  };

  return (
    <Box sx={{ maxWidth: 700, mx: 'auto', mt: 5 }}>
      <Typography variant="h3" sx={{ textAlign: 'center', mb: 1 }}>
        Authors
      </Typography>
      <Typography sx={{ textAlign: 'center', color: 'text.secondary', mb: 4 }}>
        Discover the people writing on BlogApp.
      </Typography>

      <TextField
        value={search}
        onChange={handleSearchChange}
        fullWidth
        placeholder="Search by name or email..."
        type="search"
        size="small"
        sx={{ mb: 4, backgroundColor: 'background.paper' }}
      />

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {users.slice(0, visibleCount).map((user) => (
            <Card key={user.id}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, '&:last-child': { pb: 2 } }}>
                <Avatar src={user.profile_picture_url} alt={user.name} sx={{ width: 48, height: 48 }}>
                  {(user.name || user.email || '?')[0].toUpperCase()}
                </Avatar>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography sx={{ fontWeight: 600 }}>{user.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {user.email} · {user.postCount} {user.postCount === 1 ? 'post' : 'posts'}
                  </Typography>
                </Box>
                <Button variant="outlined" onClick={() => navigate(`/user-posts/${user.id}`)}>
                  View posts
                </Button>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      {!loading && users.length > visibleCount && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <Button variant="contained" onClick={() => setVisibleCount(prev => prev + 10)}>
            Load More
          </Button>
        </Box>
      )}
    </Box>
  );
}

export default UsersPage;
