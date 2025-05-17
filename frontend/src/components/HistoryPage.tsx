import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Clock, Search, Trash2, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getQueryHistory, deleteQueryHistory } from '@/lib/api';

interface HistoryItem {
  id: string;
  query: string;
  sql: string;
  timestamp: string;
  conversation_id?: string;
}

export function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getQueryHistory();
      setHistory(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching history:', err);
      setError('Failed to load query history. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteQueryHistory(id);
      setHistory(prevHistory => prevHistory.filter(item => item.id !== id));
      if (selectedItem?.id === id) {
        setSelectedItem(null);
      }
    } catch (err) {
      console.error('Error deleting history item:', err);
      setError('Failed to delete the query. Please try again.');
    }
  };

  const filteredHistory = history.filter(item => 
    item.query.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      hour12: true
    }).format(date);
  };

  return (
    <div className="flex-1 p-6 overflow-auto bg-black/30 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent mb-2">
            Query History
          </h1>
          <p className="text-gray-400">
            View and manage your past queries and conversations.
          </p>
        </header>

        {/* Search Bar */}
        <div className="relative mb-6">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search your query history..."
            className="block w-full pl-10 pr-3 py-2 bg-white/[0.03] border border-white/10 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-500/20 text-red-300 p-4 rounded-md mb-6">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
          </div>
        ) : (
          <>
            {filteredHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center text-center py-16">
                <Clock className="w-12 h-12 text-gray-500 mb-4" />
                <h3 className="text-xl font-medium text-gray-300 mb-2">No Queries Found</h3>
                <p className="text-gray-400 max-w-md">
                  {searchTerm ? 
                    "No queries match your search. Try a different search term." : 
                    "You haven't made any queries yet. Start by asking a question in the chat."}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-1 space-y-2 pr-4 border-r border-white/[0.05]">
                  <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-indigo-400" />
                    Recent Queries
                  </h2>
                  <div className="space-y-2 max-h-[calc(100vh-240px)] overflow-y-auto pr-2 pb-4">
                    {filteredHistory.map((item) => (
                      <motion.div
                        key={item.id}
                        className={cn(
                          "p-3 rounded-lg cursor-pointer transition-colors",
                          selectedItem?.id === item.id 
                            ? "bg-indigo-500/20 border border-indigo-500/30" 
                            : "bg-white/[0.03] border border-white/[0.05] hover:bg-white/[0.05]"
                        )}
                        onClick={() => setSelectedItem(item)}
                        whileHover={{ scale: 1.01 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div className="flex justify-between items-start mb-1">
                          <div className="text-sm text-gray-400">
                            {formatDate(item.timestamp)}
                          </div>
                          <button
                            onClick={(e) => handleDelete(item.id, e)}
                            className="text-gray-500 hover:text-red-400 transition-colors"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                        <div className="text-sm text-white font-medium line-clamp-2">
                          {item.query}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>

                <div className="md:col-span-2">
                  {selectedItem ? (
                    <div className="space-y-6">
                      <div>
                        <h3 className="text-lg font-medium text-white mb-2">Query</h3>
                        <div className="p-4 bg-white/[0.03] border border-white/[0.05] rounded-lg">
                          <p className="text-white">{selectedItem.query}</p>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-medium text-white mb-2">Generated SQL</h3>
                        <div className="p-4 bg-black/80 border border-white/[0.05] rounded-lg">
                          <pre className="text-indigo-300 text-sm font-mono whitespace-pre-wrap">
                            {selectedItem.sql}
                          </pre>
                        </div>
                      </div>

                      <div className="flex justify-end">
                        <button
                          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md transition-colors"
                          onClick={() => {
                            if (selectedItem.conversation_id) {
                              // Navigate to the chat with the conversation ID
                              window.location.href = `/dashboard?conversation=${selectedItem.conversation_id}`;
                            }
                          }}
                          disabled={!selectedItem.conversation_id}
                        >
                          Continue Conversation
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full py-16 text-center">
                      <MessageSquare className="w-12 h-12 text-gray-500 mb-4" />
                      <h3 className="text-xl font-medium text-gray-300 mb-2">Select a Query</h3>
                      <p className="text-gray-400 max-w-md">
                        Click on a query from the list to view details and continue the conversation.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
} 