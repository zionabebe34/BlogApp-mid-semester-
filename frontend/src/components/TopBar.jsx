import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { Link, useNavigate } from 'react-router-dom';

function TopBar({ currentUser, setCurrentUser }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await fetch('/api/logout', {
      method: 'POST',
      credentials: 'include'
    });
    setCurrentUser(null);
    navigate('/Login');
  };

  // 1. Dynamic nav items: filter out 'Login' if user is logged in
  const navItems = currentUser
    ? ['Home', 'Users', 'Profile', 'About']
    : ['Home', 'Users', 'About', 'Login'];

  return (
    // 2. Add zIndex to Box/AppBar to ensure it stays above content
    <Box sx={{ display: 'flex', zIndex: 1200, position: 'relative' }}>
      <AppBar component="nav" sx={{ backgroundColor: '#5b6dfa', zIndex: 1200 }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ fontWeight: 700, mr: 2 }}>
            MyApp
          </Typography>
          
          {/* New Post Button - only show if logged in */}
          {currentUser && (
            <Button component={Link} to="/new-post" variant="contained" sx={{ background: '#f5a623', color: '#000' }}>
              + New Post
            </Button>
          )}

          <Box sx={{ flexGrow: 1 }} />
          
          <Box>
            {navItems.map((item) => (
              <Button key={item} sx={{ color: '#fff' }} component={Link} to={`/${item === 'Home' ? '' : item.toLowerCase()}`}>
                {item}
              </Button>
            ))}
          </Box>

          {currentUser && (
            <Box sx={{ ml: 2, textAlign: 'right' }}>
              <Typography variant="body2" sx={{ color: '#fff' }}>{currentUser.email}</Typography>
              <Button onClick={handleLogout} sx={{ color: '#f5a623', p: 0, minWidth: 0, fontSize: 12 }}>
                Logout
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>
      {/* Spacer to prevent content from going under the fixed navbar */}
      <Toolbar /> 
    </Box>
  );
}

export default TopBar;