import { useEffect, useState } from 'react';
import axios from 'axios';

export default function ViewArticles() {
  const [articles, setArticles] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [feedbackFormVisible, setFeedbackFormVisible] = useState(null);
  const [feedbackData, setFeedbackData] = useState({ comment: '', rating: '' });
  const [editingFeedback, setEditingFeedback] = useState(null);
  const [editData, setEditData] = useState({ comment: '', rating: '' });

  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('userId');

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
        headers: { Authorization: `Bearer ${token}` },
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

  const handleFeedbackSubmit = async (id) => {
    const { comment, rating } = feedbackData;
    if (!comment || !rating) return alert("Please fill both fields.");
    try {
      await axios.post(
        `/api/articles/${id}/feedback`,
        { comment, rating: parseInt(rating) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('Feedback submitted!');
      setFeedbackFormVisible(null);
      setFeedbackData({ comment: '', rating: '' });
      fetchArticles();
    } catch (err) {
      console.error('Error in sending feedback:', err);
    }
  };

  const deleteFeedback = async (articleId, feedbackId) => {
    try {
      await axios.delete(`/api/articles/${articleId}/feedbacks/${feedbackId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchArticles();
    } catch (err) {
      console.error('Error deleting feedback:', err);
    }
  };

  const handleEditClick = (feedback) => {
    setEditingFeedback(feedback._id);
    setEditData({ comment: feedback.comment, rating: feedback.rating });
  };

  const handleEditSubmit = async (articleId, feedbackId) => {
    const { comment, rating } = editData;
    if (!comment || !rating) return alert("Please fill both fields.");
    try {
      await axios.put(
        `/api/articles/${articleId}/feedbacks/${feedbackId}`,
        { comment, rating: parseInt(rating) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setEditingFeedback(null);
      setEditData({ comment: '', rating: '' });
      fetchArticles();
    } catch (err) {
      console.error('Error updating feedback:', err);
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
              <p><strong>Published Date:</strong> {article.publishedDate ? article.publishedDate.slice(0, 10) : 'N/A'}</p>
              <p><strong>Source:</strong> {article.sourceName}</p>
              <p><strong>Publisher:</strong> {article.owner?.username || 'Unknown'}</p>
              <p><strong>Content:</strong>{' '}
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
              className="mt-2 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
              onClick={() => setFeedbackFormVisible(article._id)}
            >
              Leave Feedback
            </button>

            {feedbackFormVisible === article._id && (
              <div className="mt-3 p-3 bg-gray-100 rounded space-y-2">
                <textarea
                  placeholder="Write your feedback..."
                  className="w-full border p-2 rounded"
                  value={feedbackData.comment}
                  onChange={(e) => setFeedbackData({ ...feedbackData, comment: e.target.value })}
                />
                <input
                  type="number"
                  placeholder="Rating (1-5)"
                  className="w-full border p-2 rounded"
                  min="1"
                  max="5"
                  value={feedbackData.rating}
                  onChange={(e) => setFeedbackData({ ...feedbackData, rating: e.target.value })}
                />
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleFeedbackSubmit(article._id)}
                    className="px-4 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Submit
                  </button>
                  <button
                    onClick={() => setFeedbackFormVisible(null)}
                    className="px-4 py-1 bg-gray-400 text-white rounded hover:bg-gray-500"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {article.feedbacks && article.feedbacks.length > 0 && (
              <div className="mt-3 bg-gray-50 p-3 rounded">
                <h4 className="text-md font-semibold mb-2">Feedbacks:</h4>
                <ul>
                  {article.feedbacks.map((fb) => (
                    <li key={fb._id} className="border-b py-2">
                      {editingFeedback === fb._id ? (
                        <div className="space-y-2">
                          <textarea
                            value={editData.comment}
                            onChange={(e) => setEditData({ ...editData, comment: e.target.value })}
                            className="w-full border p-2 rounded"
                          />
                          <input
                            type="number"
                            min="1"
                            max="5"
                            value={editData.rating}
                            onChange={(e) => setEditData({ ...editData, rating: e.target.value })}
                            className="w-full border p-2 rounded"
                          />
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleEditSubmit(article._id, fb._id)}
                              className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => setEditingFeedback(null)}
                              className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-between items-center">
                          <span>
                            <strong>{fb.owner?.username || 'Anonymous'}</strong> ({fb.rating}/5): {fb.comment}
                          </span>
                          {currentUser && fb.owner?._id === currentUser._id && (
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleEditClick(fb)}
                                className="bg-yellow-500 text-white px-2 py-1 rounded hover:bg-yellow-600"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => deleteFeedback(article._id, fb._id)}
                                className="bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600"
                              >
                                Delete
                              </button>
                            </div>
                          )}
                        </div>
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
