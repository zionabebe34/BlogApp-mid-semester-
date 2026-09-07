import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Avatar from '@mui/material/Avatar';
import { Link, useNavigate } from 'react-router-dom';
import { logout } from '../api';

/**
 * Site header, shown on every page:
 * serif "BlogApp" logo on the left, nav links + a Write button on the right,
 * and the logged-in user's avatar with a logout action.
 */
function TopBar({ currentUser, setCurrentUser }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    setCurrentUser(null);
    navigate('/Login');
  };

  // "Login" only shows for visitors; "Profile" only for logged-in users
  const navLinks = currentUser
    ? [
        { label: 'Home', to: '/Home' },
        { label: 'Authors', to: '/Users' },
        { label: 'Profile', to: '/profile' },
        { label: 'About', to: '/About' },
      ]
    : [
        { label: 'Home', to: '/Home' },
        { label: 'Authors', to: '/Users' },
        { label: 'About', to: '/About' },
        { label: 'Login', to: '/Login' },
      ];

  return (
    <>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          backgroundColor: 'background.paper',
          color: 'text.primary',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Toolbar sx={{ maxWidth: 1100, width: '100%', mx: 'auto' }}>
          {/* Logo */}
          <Typography
            component={Link}
            to="/Home"
            variant="h5"
            sx={{ color: 'text.primary', textDecoration: 'none', letterSpacing: '-0.5px' }}
          >
            HandyHub<Box component="span" sx={{ color: 'secondary.main' }}>.</Box>
          </Typography>

          <Box sx={{ flexGrow: 1 }} />

          {/* Nav links */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {navLinks.map(({ label, to }) => (
              <Button key={label} component={Link} to={to} sx={{ color: 'text.secondary', px: 1.5 }}>
                {label}
              </Button>
            ))}
          </Box>

          {currentUser && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, ml: 2 }}>
              <Button component={Link} to="/new-post" variant="contained" sx={{ px: 2.5, whiteSpace: 'nowrap' }}>
                ✎ Write
              </Button>
              <Avatar sx={{ width: 34, height: 34, bgcolor: 'secondary.main', fontSize: 15 }}>
                {(currentUser.name || currentUser.email || '?')[0].toUpperCase()}
              </Avatar>
              <Button onClick={handleLogout} size="small" sx={{ color: 'text.secondary', minWidth: 0 }}>
                Logout
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Spacer so page content starts below the fixed header */}
      <Toolbar />
    </>
  );
}

export default TopBar;
