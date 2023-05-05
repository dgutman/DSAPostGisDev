'use strict';

(function() {
  window.App = window.App || {};

  var data = [
    { id: 1, sales: 20, year: '02' },
    { id: 2, sales: 55, year: '03' },
    { id: 3, sales: 40, year: '04' },
    { id: 4, sales: 78, year: '05' },
    { id: 5, sales: 61, year: '06' },
    { id: 6, sales: 35, year: '07' },
    { id: 7, sales: 80, year: '08' },
    { id: 8, sales: 50, year: '09' },
    { id: 9, sales: 65, year: '10' },
    { id: 10, sales: 59, year: '11' }
  ];

  var histCharts = {
    margin: 20,
    width: 550,
    rows: [
      {
        view: 'chart',
        type: 'line',
        value: '#sales#',
        line: {
          width: 3
        },
        xAxis: {
          template: "'#year#"
        },
        offset: 0,
        yAxis: {
          start: 0,
          end: 100,
          step: 10,
          template: function(obj) {
            return obj % 20 ? '' : obj;
          }
        },
        data: data,
        height: 300
      },
      {
        view: 'chart',
        type: 'spline',
        value: '#sales#',
        item: {
          borderColor: '#ffffff',
          color: '#000000'
        },
        line: {
          color: '#ff9900',
          width: 3
        },
        xAxis: {
          template: "'#year#"
        },
        offset: 0,
        yAxis: {
          start: 0,
          end: 100,
          step: 10,
          template: function(obj) {
            return obj % 20 ? '' : obj;
          }
        },
        data: data,
        height: 300
      }
    ]
  };

  App.webixFunctions = { hello: 'world', how: 'areYou', wbxHistChart: histCharts };
})();
