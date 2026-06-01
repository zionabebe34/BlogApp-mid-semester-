import { Box, Typography, Card, CardContent } from '@mui/material';

function About() {
    return (
        <Box sx={{ maxWidth: 700, mx: 'auto', mt: 8 }}>
            <Card sx={{ borderRadius: 3, boxShadow: 2, p: 2 }}>
                <CardContent>
                    <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
                        About MyApp
                    </Typography>
                    <Typography variant="body1" sx={{ color: 'text.secondary', mb: 2 }}>
                        MyApp is a social feed application where users can browse posts, explore user profiles, and create new content.
                    </Typography>
                    <Typography variant="body1" sx={{ color: 'text.secondary', mb: 2 }}>
                        You can browse the feed to read posts from various users, search users by email, and view all posts from a specific user.
                    </Typography>
                    <Typography variant="body1" sx={{ color: 'text.secondary' }}>
                        Built with React, Material UI, and the JSONPlaceholder API.
                    </Typography>
                </CardContent>
            </Card>
        </Box>
    );
}

export default About;
