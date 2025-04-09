import React, { useEffect, useRef, useState } from 'react';
import Chart from 'chart.js/auto';  // Use /auto to register all controllers and scales

const SkillsChart = ({ professional, category }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    // Generate chart data based on professional and category
    if (professional) {
      let labels = [];
      let data = [];
      
      // Determine what data to display based on category
      if (category && category.includes('Medical')) {
        labels = ['Expertise', 'Experience', 'Reputation', 'Availability', 'Patient Reviews'];
        // Generate random scores between 70 and 100 for demo purposes
        data = [
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
        ];
      } else if (category && category.includes('Legal')) {
        labels = ['Expertise', 'Case Success', 'Experience', 'Reputation', 'Client Reviews'];
        data = [
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
        ];
      } else if (category && category.includes('CS')) {
        labels = ['Technical Skills', 'Problem Solving', 'Communication', 'Project Management', 'Code Quality'];
        data = [
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
        ];
      } else {
        labels = ['Expertise', 'Experience', 'Service Quality', 'Value', 'Customer Satisfaction'];
        data = [
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
          Math.floor(Math.random() * 30) + 70,
        ];
      }
      
      setChartData({ labels, data });
    }
  }, [professional, category]);

  useEffect(() => {
    // Create or update chart when data changes
    if (chartData && chartRef.current) {
      // Destroy previous chart instance if it exists
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
      
      // Create new chart
      const ctx = chartRef.current.getContext('2d');
      chartInstance.current = new Chart(ctx, {
        type: 'radar',
        data: {
          labels: chartData.labels,
          datasets: [{
            label: 'Skills Rating',
            data: chartData.data,
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(54, 162, 235, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
          }]
        },
        options: {
          scales: {
            r: {
              angleLines: {
                display: true
              },
              suggestedMin: 0,
              suggestedMax: 100
            }
          },
          plugins: {
            title: {
              display: true,
              text: 'Professional Skills Profile',
              font: {
                size: 16
              }
            },
            legend: {
              display: false
            }
          },
          maintainAspectRatio: false
        }
      });
    }
    
    // Cleanup function to destroy chart when component unmounts
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [chartData]);

  return (
    <div className="skills-chart">
      <h3>Skills Profile</h3>
      <div className="chart-container" style={{ height: '300px', width: '100%' }}>
        <canvas ref={chartRef} />
      </div>
    </div>
  );
};

export default SkillsChart;