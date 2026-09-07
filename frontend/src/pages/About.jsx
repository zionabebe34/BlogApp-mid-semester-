import { Box, Typography, Card, CardContent } from '@mui/material';

function About() {
  return (
    <Box sx={{ maxWidth: 700, mx: 'auto', mt: 6 }}>
      <Card sx={{ p: 2 }}>
        <CardContent>
          <Typography variant="h4" sx={{ mb: 2 }}>
            About BlogApp
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary', mb: 2 }}>
            BlogApp is a place to read, write and share stories. Browse the
            latest posts on the home feed, follow the authors you enjoy, and
            build a personal feed made just from the people you follow.
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary', mb: 2 }}>
            Anyone can read — create an account to write your own posts with
            a rich-text editor, add a cover image, and grow your audience.
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>
            Built with React and Material UI on the frontend, and Flask with
            MySQL on the backend.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default About;
