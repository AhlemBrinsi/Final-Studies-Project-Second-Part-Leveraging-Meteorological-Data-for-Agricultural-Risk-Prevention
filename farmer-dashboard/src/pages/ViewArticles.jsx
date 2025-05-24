import { useEffect, useState } from 'react';
import axios from 'axios';



export default function ViewArticles() {
  const [articles, setArticles] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
const userId = localStorage.getItem('userId');
const token = localStorage.getItem('token');




const fetchCurrentUser = async () => {
  if (!userId) return;

  try {
    const response = await axios.get(`http://localhost:5173/api/users/${userId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    setCurrentUser(response.data);
  } catch (error) {
    console.error('Error fetching current user:', error);
  }
};

  const fetchArticles = async () => {
    try {
      const res = await axios.get('/api/articles', {
            headers: {
            Authorization: `Bearer ${token}`,  // <-- use backticks here
            },
        });
      setArticles(res.data);
    } catch (err) {
      console.error('Error fetching articles:', err);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      await fetchArticles();
      await fetchCurrentUser();
    };
    loadData();
  }, []);

  const sendFeedback = async (id) => {
    const comment = prompt('Enter your feedback:');
    const rating = prompt('Rating (1-5):');
    if (!comment || !rating) return;
    try {
      await axios.post(
        `/api/articles/${id}/feedback`,
        { comment, rating: parseInt(rating) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('Feedback submitted!');
      fetchArticles();
    } catch (err) {
      console.error('Error in sending feedback:', err);
    }
  };

  const deleteFeedback = async (articleId, feedbackId) => {
    try {
      await axios.delete(
        `/api/articles/${articleId}/feedbacks/${feedbackId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      fetchArticles();
    } catch (err) {
      console.error('Error deleting feedback:', err);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Articles</h2>
      <ul>
        {articles.map((article) => (
          <li key={article._id} className="mb-4 border p-3 rounded">
            <div>
<p><strong>Title:</strong> {article.title}</p>
                <p><strong>Author:</strong> {article.authorName}</p>
                <p><strong>Published Date:</strong> {article.publishedDate ? article.publishedDate.slice(0,10) : 'N/A'}</p>
                <p><strong>Source:</strong> {article.sourceName}</p>
                <p><strong>Publisher:</strong> {article.owner?.username || 'Unknown'}</p>
                <p><strong>Content:</strong> 
                  {' '}
                  {article.content ? (
                    typeof article.content === 'string' && article.content.startsWith('http') ? (
                      <a href={article.content} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                        {article.content}
                      </a>
                    ) : (
                      article.content
                    )
                  ) : (
                    'No content'
                  )}
                </p>
            </div>

            <button
              className="mt-2 px-2 py-1 bg-blue-500 text-white rounded"
              onClick={() => sendFeedback(article._id)}
            >
              Leave Feedback
            </button>

            {article.feedbacks && article.feedbacks.length > 0 && (
              <div className="mt-3 bg-gray-50 p-3 rounded">
                <h4 className="text-md font-semibold mb-2">Feedbacks:</h4>
                <ul>
                  {article.feedbacks.map((fb) => (
                    <li key={fb._id} className="border-b py-2 flex justify-between items-center">
                      <span>
                        <strong>{fb.owner?.username || 'Anonymous'}</strong> ({fb.rating}/5): {fb.comment}
                      </span>
                      {currentUser && fb.owner?._id === currentUser._id && (
                        <button
                          onClick={() => deleteFeedback(article._id, fb._id)}
                          className="hover:opacity-100 flex items-center ml-2 bg-red-500 text-white rounded "
                        >
                          Delete
                        </button>
                      )}
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
