import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Card, CardContent, Typography, TextField, Button } from '@mui/material';

function Signup() {
    const navigate = useNavigate();
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [repeatPassword, setRepeatPassword] = useState('');

    const handleSignup = async (e) => {
        e.preventDefault();
        if (password !== repeatPassword) {
            alert('Passwords do not match!');
            return;
        }
        
        const response = await fetch('/api/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include', // Include cookies for session management
            body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();
        
        if (response.ok) {
            // Signup successful
            navigate('/Login');
        } else {
            // Signup failed
            alert('Signup failed: ' + data.message);

        }
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mt: 10 }}>
            <Card sx={{ width: 400, borderRadius: 3, boxShadow: 3, p: 2 }}>
                <CardContent>
                    <Typography variant="h5" sx={{ fontWeight: 700, textAlign: 'center', mb: 0.5 }}>
                        Create Account
                    </Typography>
                    <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary', mb: 3 }}>
                        Sign up for a new account
                    </Typography>

                    <form onSubmit={handleSignup}>
                        <Typography variant="body2" sx={{ mb: 0.5 }}>Name</Typography>
                        <TextField
                            fullWidth
                            placeholder="Your name"
                            type="text"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            size="small"
                            sx={{ mb: 2 }}
                        />

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
                            sx={{ mb: 2 }}
                        />

                        <Typography variant="body2" sx={{ mb: 0.5 }}>Repeat Password</Typography>
                        <TextField
                            fullWidth
                            placeholder="••••••••"
                            type="password"
                            value={repeatPassword}
                            onChange={e => setRepeatPassword(e.target.value)}
                            size="small"
                            sx={{ mb: 3 }}
                        />

                        <Button
                            fullWidth
                            type="submit"
                            variant="contained"
                            sx={{ background: '#5b6dfa', borderRadius: 2, fontWeight: 600, mb: 2 }}
                        >
                            Sign Up
                        </Button>
                    </form>

                    <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary' }}>
                        Already have an account?{' '}
                        <span
                            onClick={() => navigate('/Login')}
                            style={{ color: '#5b6dfa', cursor: 'pointer', fontWeight: 600 }}
                        >
                            Login
                        </span>
                    </Typography>
                </CardContent>
            </Card>
        </Box>
    );
}

export default Signup;
