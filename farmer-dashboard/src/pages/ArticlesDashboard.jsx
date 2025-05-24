import { useEffect, useState } from 'react';
import axios from 'axios';

export default function ArticlesDashboard() {
  const [articles, setArticles] = useState([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [authorName, setAuthorName] = useState('');
  const [publishedDate, setDate] = useState('');
  const [sourceName, setSource] = useState('');
  const [editArticleId, setEditArticleId] = useState(null);
  const [editData, setEditData] = useState({});
  const [contentInputType, setContentInputType] = useState('write'); // for edit mode content input type
  // Add this state to manage content input type for creation
  const [newContentInputType, setNewContentInputType] = useState('write');


  // Confirmation modal state
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [articleToDelete, setArticleToDelete] = useState(null);

  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('userId');

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
        { title, authorName, publishedDate, sourceName, content,userId },
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

  // Start editing an article
  const startEditing = (article) => {
    setEditArticleId(article._id);
    setEditData({
      title: article.title,
      authorName: article.authorName,
      publishedDate: article.publishedDate ? article.publishedDate.slice(0,10) : '',
      sourceName: article.sourceName,
      content: article.content,
    });

    // Determine initial content input type based on content format
    if (typeof article.content === 'string') {
      if (article.content.startsWith('http')) {
        setContentInputType('url');
      } else {
        setContentInputType('write');
      }
    } else {
      setContentInputType('write'); // fallback
    }
  };

  const cancelEditing = () => {
    setEditArticleId(null);
    setEditData({});
    setContentInputType('write');
  };

  const saveEditing = async () => {
    try {
      await axios.put(
        `/api/articles/${editArticleId}`,
        editData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      setEditArticleId(null);
      setEditData({});
      setContentInputType('write');
      fetchArticles();
    } catch (err) {
      console.error('Error saving article:', err);
    }
  };

  const handleEditChange = (field, value) => {
    setEditData(prev => ({ ...prev, [field]: value }));
  };

  // Handle content input type change in edit mode
  const handleContentInputTypeChange = (e) => {
    setContentInputType(e.target.value);
    // Reset content when switching types
    setEditData(prev => ({ ...prev, content: '' }));
  };

  // Show modal before delete
  const handleDeleteClick = (id) => {
    setArticleToDelete(id);
    setShowConfirmModal(true);
  };

  // Confirm delete article
  const confirmDeleteArticle = async () => {
    try {
      await axios.delete(`/api/articles/${articleToDelete}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      fetchArticles();
      setShowConfirmModal(false);
      setArticleToDelete(null);
    } catch (error) {
      console.error("Error deleting article:", error);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold">Manage Articles</h2>

    {/* Create new article inputs */}
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
        type="date"
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

      {/* Content input type selection */}
      <div className="mb-2">
        <label className="mr-3">
          <input
            type="radio"
            name="newContentInputType"
            value="write"
            checked={newContentInputType === 'write'}
            onChange={e => {
              setNewContentInputType(e.target.value);
              setContent('');
            }}
          /> Write
        </label>
        <label>
          <input
            type="radio"
            name="newContentInputType"
            value="url"
            checked={newContentInputType === 'url'}
            onChange={e => {
              setNewContentInputType(e.target.value);
              setContent('');
            }}
          /> URL
        </label>
      </div>

      {/* Content input area based on selected type */}
      {newContentInputType === 'write' && (
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder="Write content here"
          className="border p-2 mr-2 w-96 h-24 inline-block align-top"
        />
      )}
      {newContentInputType === 'url' && (
        <input
          type="url"
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder="Paste URL here"
          className="border p-2 mr-2 w-96 inline-block align-top"
        />
      )}

      <button
        onClick={createArticle}
        className="bg-green-500 text-white px-3 py-1 rounded"
      >
        Add
      </button>
    </div>
      {/* List articles */}

      <ul>
        {articles.map(article => {
          const isOwner = String(article.owner?._id) === String(userId);
          return (
            <li key={article._id} className="mb-4 border p-3 rounded">
              {editArticleId === article._id ? (
                // Edit mode
                <>
                  <input
                    value={editData.title}
                    onChange={e => handleEditChange('title', e.target.value)}
                    placeholder="Title"
                    className="border p-1 mb-1 w-full"
                  />
                  <input
                    value={editData.authorName}
                    onChange={e => handleEditChange('authorName', e.target.value)}
                    placeholder="Author"
                    className="border p-1 mb-1 w-full"
                  />
                  <input
                    type="date"
                    value={editData.publishedDate ? editData.publishedDate.slice(0,10) : ''}
                    onChange={e => handleEditChange('publishedDate', e.target.value)}
                    className="border p-1 mb-1 w-full"
                  />
                  <input
                    value={editData.sourceName}
                    onChange={e => handleEditChange('sourceName', e.target.value)}
                    placeholder="Source"
                    className="border p-1 mb-1 w-full"
                  />

                  {/* Content input type selection */}
                  <div className="mb-2">
                    <label className="mr-3">
                      <input
                        type="radio"
                        name={`contentInputType-${article._id}`}
                        value="write"
                        checked={contentInputType === 'write'}
                        onChange={handleContentInputTypeChange}
                      /> Write
                    </label>
                    <label>
                      <input
                        type="radio"
                        name={`contentInputType-${article._id}`}
                        value="url"
                        checked={contentInputType === 'url'}
                        onChange={handleContentInputTypeChange}
                      /> URL
                    </label>
                  </div>

                  {/* Content input area */}
                  {contentInputType === 'write' && (
                    <textarea
                      value={editData.content}
                      onChange={e => handleEditChange('content', e.target.value)}
                      placeholder="Write content here"
                      className="border p-2 mb-2 w-full h-24"
                    />
                  )}

                  {contentInputType === 'url' && (
                    <input
                      type="url"
                      value={editData.content}
                      onChange={e => handleEditChange('content', e.target.value)}
                      placeholder="Paste URL here"
                      className="border p-2 mb-2 w-full"
                    />
                  )}

                  <div>
                    <button
                      onClick={saveEditing}
                      className="bg-blue-600 text-white px-3 py-1 rounded mr-2"
                    >
                      Save
                    </button>
                    <button
                      onClick={cancelEditing}
                      className="bg-gray-400 text-white px-3 py-1 rounded"
                    >
                      Cancel
                    </button>
                  </div>
                </>
              ) : (
                // Display mode
                <>
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
                  {isOwner && (
                    <>
                      <button
                        onClick={() => startEditing(article)}
                        className="text-blue-600 mr-2"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteClick(article._id)}
                        className="text-red-600"
                      >
                        Delete
                      </button>
                    </>
                  )}
                </>
              )}
            </li>
          );
        })}
      </ul>


      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg w-96">
            <h2 className="text-xl font-bold mb-4">Confirm Deletion</h2>
            <p>Are you sure you want to delete this article?</p>
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="bg-gray-300 text-gray-800 px-4 py-2 rounded mr-2"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteArticle}
                className="bg-red-600 text-white px-4 py-2 rounded"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
