import React, { useEffect, useState } from 'react';
import Papa from 'papaparse';

const CsvFetcher = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchCsv = async () => {
      const response = await fetch('/merged_product_data.csv'); // Use the correct path to your CSV file
      const text = await response.text();

      Papa.parse(text, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          console.log(results.data); // This will be your JSON data
          setData(results.data);
        },
        error: (error) => {
          console.error('Error fetching or parsing CSV:', error);
        },
      });
    };

    fetchCsv();
  }, []); // This effect runs once on component mount

  return (
    <div>
      <h2>CSV Data in JSON Format:</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>{' '}
      {/* Display parsed data in JSON format */}
    </div>
  );
};

export default CsvFetcher;
