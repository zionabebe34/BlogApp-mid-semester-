import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, Card, CardContent, Typography, TextField, Button } from '@mui/material';
import { resetPassword } from '../api';

/**
 * Consumes the `?token=` from the reset email link and sets a new password.
 * The token itself is opaque to us — the backend is the only one that can
 * tell whether it's valid, unused, and not expired.
 */
function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== repeatPassword) {
      setError('Passwords do not match!');
      return;
    }

    try {
      await resetPassword(token, password);
      setError('');
      setSuccess(true);
    } catch (err) {
      setError(err.message || 'Something went wrong');
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
      <Card sx={{ width: 420, p: 2 }}>
        <CardContent>
          <Typography variant="h4" sx={{ textAlign: 'center', mb: 0.5 }}>
            Choose a new password.
          </Typography>

          {!token && (
            <Typography color="error" sx={{ mb: 2, textAlign: 'center' }}>
              This link is missing a reset token.
            </Typography>
          )}

          {error && (
            <Typography color="error" sx={{ mb: 2, textAlign: 'center' }}>
              {error}
            </Typography>
          )}

          {success ? (
            <>
              <Typography sx={{ mb: 3, textAlign: 'center', color: 'success.main' }}>
                Password updated successfully. You can now log in.
              </Typography>
              <Button fullWidth variant="contained" onClick={() => navigate('/Login')}>
                Go to Login
              </Button>
            </>
          ) : (
            <form onSubmit={handleSubmit}>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>New password</Typography>
              <TextField
                fullWidth
                placeholder="••••••••"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                size="small"
                sx={{ mb: 2 }}
              />

              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Repeat password</Typography>
              <TextField
                fullWidth
                placeholder="••••••••"
                type="password"
                value={repeatPassword}
                onChange={e => setRepeatPassword(e.target.value)}
                size="small"
                sx={{ mb: 3 }}
              />

              <Button fullWidth type="submit" variant="contained" sx={{ py: 1.2 }} disabled={!token}>
                Set new password
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

export default ResetPassword;
