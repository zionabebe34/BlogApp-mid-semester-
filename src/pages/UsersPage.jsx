import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchUsersWithPostCounts } from "../api";
import { Box, TextField, Button, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';

function UsersPage() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [visibleCount, setVisibleCount] = useState(5);
    const navigate = useNavigate();
    const debounceTimer = useRef(null);

    useEffect(() => {
        async function fetchData() {
            setLoading(true);
            try {
                const usersWithCounts = await fetchUsersWithPostCounts();
                setUsers(usersWithCounts);
            } catch (e) {
                setUsers([]);
            }
            setLoading(false);
        }
        fetchData();
    }, []);

    const handleSearchChange = (e) => {
        const value = e.target.value;
        setSearch(value);
        setVisibleCount(5);

        clearTimeout(debounceTimer.current);
        debounceTimer.current = setTimeout(async () => {
            if (value.trim() === '') {
                setLoading(true);
                try {
                    const all = await fetchUsersWithPostCounts();
                    setUsers(all);
                } catch {
                    setUsers([]);
                }
                setLoading(false);
            } else {
                setLoading(true);
                try {
                    const res = await fetch(`/api/users/search?q=${encodeURIComponent(value)}`, { credentials: 'include' });
                    const data = await res.json();
                    setUsers(data.map(u => ({ ...u, postCount: u.postCount ?? 0 })));
                } catch {
                    setUsers([]);
                }
                setLoading(false);
            }
        }, 400);
    };

    const handleLoadMore = () => {
        setVisibleCount(prev => prev + 10);
    };

    return (
        <Box sx={{ maxWidth: 800, mx: 'auto', mt: 6 }}>
            <TextField
                value={search}
                onChange={handleSearchChange}
                sx={{ width: '100%', mb: 4 }}
                id="filled-search"
                label="Search by name or email..."
                type="search"
                variant="filled"
            />
            {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
                    <CircularProgress />
                </Box>
            ) : (
                <TableContainer component={Paper} sx={{ borderRadius: 3, boxShadow: 2 }}>
                    <Table>
                        <TableHead>
                            <TableRow sx={{ backgroundColor: '#f6f8fc' }}>
                                <TableCell sx={{ fontWeight: 'bold', fontSize: 18 }}>Email</TableCell>
                                <TableCell sx={{ fontWeight: 'bold', fontSize: 18 }}>Posts</TableCell>
                                <TableCell></TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {users.slice(0, visibleCount).map((user, idx) => (
                                <TableRow key={user.id} sx={{ backgroundColor: idx % 2 === 0 ? '#fff' : '#f6f8fc' }}>
                                    <TableCell>{user.email}</TableCell>
                                    <TableCell>{user.postCount}</TableCell>
                                    <TableCell>
                                        <Button
                                            variant="contained"
                                            sx={{ borderRadius: 5, background: '#5b6dfa', textTransform: 'none', fontWeight: 600 }}
                                            onClick={() => navigate(`/user-posts/${user.id}`)}
                                        >
                                            See Posts
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}
            {!loading && users.length > visibleCount && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                    <Button variant="contained" onClick={handleLoadMore}>
                        Load More
                    </Button>
                </Box>
            )}
        </Box>
    );
}

export default UsersPage;
