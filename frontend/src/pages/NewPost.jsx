import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Card, CardContent, Typography, TextField, Button } from '@mui/material';
import ReactQuill from 'react-quill-new';
import 'react-quill-new/dist/quill.snow.css';

// Toolbar config for the WYSIWYG editor: bold, italic, lists, and links.
const quillModules = {
  toolbar: [
    ['bold', 'italic', 'underline'],
    [{ list: 'ordered' }, { list: 'bullet' }],
    ['link'],
    ['clean'],
  ],
};

function NewPost() {
    const navigate = useNavigate();
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [imageUrl, setImageUrl] = useState('');

    const handlePublish = async (e) => {
        e.preventDefault();

        // Send new post data to the backend (body is rich-text HTML)
        const response = await fetch('/api/new-post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ title, body, image_url: imageUrl || null })
        });

        const data = await response.json();

        if (response.ok) {
            navigate('/Home');
        } else {
            alert('Failed to create post: ' + data.message);
        }
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 6 }}>
            <Card sx={{ width: '100%', maxWidth: 700, borderRadius: 3, boxShadow: 2, p: 1 }}>
                <CardContent>
                    <Typography variant="h5" sx={{ fontWeight: 700, textAlign: 'center', mb: 4 }}>
                        Create New Post
                    </Typography>

                    <form onSubmit={handlePublish}>
                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Title</Typography>
                        <TextField
                            fullWidth
                            placeholder="Enter post title..."
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                            size="small"
                            sx={{ mb: 3 }}
                        />

                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Image URL (optional)</Typography>
                        <TextField
                            fullWidth
                            placeholder="https://example.com/photo.jpg"
                            value={imageUrl}
                            onChange={e => setImageUrl(e.target.value)}
                            size="small"
                            sx={{ mb: 1 }}
                        />
                        {imageUrl && (
                            <Box
                                component="img"
                                src={imageUrl}
                                alt="preview"
                                sx={{ width: '100%', maxHeight: 200, objectFit: 'cover', borderRadius: 2, mb: 3 }}
                            />
                        )}

                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Body</Typography>
                        <Box sx={{ mb: 6 }}>
                            <ReactQuill
                                theme="snow"
                                value={body}
                                onChange={setBody}
                                modules={quillModules}
                                placeholder="Write your post content here..."
                                style={{ height: 200 }}
                            />
                        </Box>

                        <Button
                            fullWidth
                            type="submit"
                            variant="contained"
                            sx={{ background: '#5b6dfa', borderRadius: 2, fontWeight: 700, py: 1.5, fontSize: 16 }}
                        >
                            Publish
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </Box>
    );
}

export default NewPost;
