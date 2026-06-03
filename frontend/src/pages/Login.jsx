import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Card, CardContent, Typography, TextField, Button, Divider } from '@mui/material';

function Login({ setCurrentUser }) {

    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include', // Include cookies for session management
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            setCurrentUser({ email: data.email, name: data.name });
            navigate('/Home');
            setError('');
        } else {
            // Login failed
            setError(data.message || 'Login failed');
        }
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mt: 10 }}>
            <Card sx={{ width: 400, borderRadius: 3, boxShadow: 3, p: 2 }}>
                <CardContent>
                    <Typography variant="h5" sx={{ fontWeight: 700, textAlign: 'center', mb: 0.5 }}>
                        Welcome Back
                    </Typography>
                    <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary', mb: 3 }}>
                        Sign in to your account
                    </Typography>

                    {error && (
                        <Typography color="error" sx={{ mb: 2, textAlign: 'center' }}>
                            {error}
                        </Typography>
                    )}

                    <form onSubmit={handleLogin}>
                        <Typography variant="body2" sx={{ mb: 0.5 }}>Email</Typography>
                        <TextField
                            fullWidth
                            placeholder="you@example.com"
                            type="email"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            size="small"
                            sx={{ mb: 2 }}
                        />

                        <Typography variant="body2" sx={{ mb: 0.5 }}>Password</Typography>
                        <TextField
                            fullWidth
                            placeholder="••••••••"
                            type="password"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            size="small"
                            sx={{ mb: 3 }}
                        />

                        <Button
                            fullWidth
                            type="submit"
                            variant="contained"
                            sx={{ background: '#5b6dfa', borderRadius: 2, fontWeight: 600, mb: 2 }}
                        >
                            Login
                        </Button>
                    </form>

                    <Divider sx={{ mb: 2 }}>OR</Divider>

                    <Button
                        fullWidth
                        variant="outlined"
                        sx={{ borderRadius: 2, fontWeight: 600, color: '#5b6dfa', borderColor: '#5b6dfa' }}
                        onClick={() => navigate('/Signup')}
                    >
                        Sign Up
                    </Button>
                </CardContent>
            </Card>
        </Box>
    );
}

export default Login;
