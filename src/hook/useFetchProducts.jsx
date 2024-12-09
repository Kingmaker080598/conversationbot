import { useState, useEffect } from 'react';

const useFetchProducts = (query, nResults = 5) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/retrieve?query=${query}&n_results=${nResults}`
        );
        if (!response.ok) {
          throw new Error('Failed to fetch products');
        }
        const result = await response.json();
        setData(result.top_results || []);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    if (query) {
      fetchProducts();
    }
  }, [query, nResults]);

  return { data, loading, error };
};

export default useFetchProducts;
