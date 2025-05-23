import { useEffect, useState } from 'react';
import axios from 'axios';

export default function ArticlesDashboard() {
  const [articles, setArticles] = useState([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [authorName, setAuthorName] = useState('');
  const [publishedDate, setDate] = useState('');
  const [sourceName, setSource] = useState('');

  const token = localStorage.getItem('token');

  async function fetchArticles() {
    try {
      const response = await axios.get('/api/articles', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = response.data;
      if (!Array.isArray(data)) {
        throw new Error('Invalid data format: expected an array');
      }
      const filteredArticles = data.filter(article => article && article._id);
      setArticles(filteredArticles);
    } catch (error) {
      console.error('Error fetching articles:', error);
    }
  }

  useEffect(() => {
    if (token) {
      fetchArticles();
    } else {
      console.warn('No token found. User might not be authenticated.');
    }
  }, [token]);

  const createArticle = async () => {
    if (!token) {
      console.error('No token available. Please log in.');
      return;
    }
    try {
      await axios.post(
        '/api/articles',
        { title, authorName, publishedDate, sourceName, content },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      setTitle('');
      setAuthorName('');
      setDate('');
      setSource('');
      setContent('');
      fetchArticles();
    } catch (err) {
      console.error('Error creating article:', err);
    }
  };

  const deleteArticle = async (id) => {
    if (!token) {
      console.error('No token available. Please log in.');
      return;
    }
    try {
      await axios.delete(`/api/articles/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      fetchArticles();
    } catch (err) {
      console.error('Error deleting article:', err);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold">Manage Articles</h2>

      <div className="mb-4">
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="Title"
          className="border p-2 mr-2"
        />
        <input
          value={authorName}
          onChange={e => setAuthorName(e.target.value)}
          placeholder="Author"
          className="border p-2 mr-2"
        />
        <input
          value={publishedDate}
          onChange={e => setDate(e.target.value)}
          placeholder="Published Date"
          className="border p-2 mr-2"
        />
        <input
          value={sourceName}
          onChange={e => setSource(e.target.value)}
          placeholder="Source"
          className="border p-2 mr-2"
        />
        <input
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder="Content"
          className="border p-2 mr-2"
        />
        <button
          onClick={createArticle}
          className="bg-green-500 text-white px-3 py-1 rounded"
        >
          Add
        </button>
      </div>

      <ul>
        {articles.map(article => (
          <li key={article._id} className="mb-4 border p-3 rounded">
            <div>
              <p><strong>Title:</strong> {article.title}</p>
              <p><strong>Author:</strong> {article.authorName}</p>
              <p><strong>Source:</strong> {article.sourceName}</p>
              <p><strong>Published Date:</strong> {new Date(article.publishedDate).toLocaleDateString()}</p>
              <p><strong>Publisher:</strong> {article.owner?.username || 'Unknown'}</p>
              <p><strong>Content:</strong> {article.content}</p>
            </div>
            <div className="mt-2 flex gap-2">
              <button
                onClick={() => deleteArticle(article._id)}
                className="bg-red-500 text-white px-2 py-1 rounded"
              >
                Delete
              </button>
            </div>

            {article.feedbacks && article.feedbacks.length > 0 && (
              <div className="mt-3 bg-gray-50 p-3 rounded">
                <h4 className="text-md font-semibold mb-2">Feedbacks:</h4>
                <ul>
                  {article.feedbacks.map(fb => (
                    <li key={fb._id} className="border-b py-2">
                      <strong>{fb.user?.username || 'Anonymous'}</strong> ({fb.rating}/5): {fb.comment}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
