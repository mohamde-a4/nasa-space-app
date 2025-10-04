async function getWeatherMonthly(city) {
  const container = document.querySelector("#weather-container");
  container.innerHTML = "Loading weather data...";

  try {
    const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?city=${encodeURIComponent(city)}&format=json`);
    const geoData = await geoRes.json();
    if (!geoData.length) {
      container.innerHTML = "City not found.";
      return;
    }

    const lat = parseFloat(geoData[0].lat);
    const lon = parseFloat(geoData[0].lon);
const today = new Date(); // current date
const day = String(today.getDate()).padStart(2, '0'); // day as 2 digits
const month = String(today.getMonth() + 1).padStart(2, '0'); // month as 2 digits
let year = today.getFullYear(); // current year

// Create a date string for today
const fullDate = `${year}${month}${day}`; // YYYYMMDD

// Subtract 1 year
const lastYear = year - 1;
const lastYearDate = `${lastYear}${month}${day}`; // same month/day, previous year
    const start = `${year}`;
    const end = `${year}`;

    const parameters = "T2M,WS2M,WD2M,PRECTOT";
    const nasaUrl = `https://power.larc.nasa.gov/api/temporal/daily/point?start=${start}&end=${end}&latitude=${lat}&longitude=${lon}&parameters=${parameters}&community=AG&format=JSON`;

    const nasaRes = await fetch(nasaUrl);
    if (!nasaRes.ok) throw new Error(`NASA POWER request failed: ${nasaRes.status}`);

    const weatherData = await nasaRes.json();
    if (!weatherData.properties || !weatherData.properties.parameter) throw new Error("No data returned from NASA POWER");

    const months = Object.keys(weatherData.properties.parameter.T2M);
    container.innerHTML = ""; // clear loading

    months.forEach((month,index) => {
      const T2M = weatherData.properties.parameter.T2M[month];
      const WS2M = weatherData.properties.parameter.WS2M[month];
      const WD2M = weatherData.properties.parameter.WD2M[month];

      let hangout = "Good to hang out";
      let cardClass = "good";
      if (T2M < 10 || T2M > 35 || WS2M > 8 ) {
        hangout = "Not ideal to hang out";
        cardClass = "bad";
      }

      const card = document.createElement("div");
      card.className = `weather-card ${cardClass}`;
      card.innerHTML = `
        <strong>${month}</strong>
        Temp: ${T2M}°C<br>
        Wind: ${WS2M} m/s (${WD2M}°)<br>
        <em>${hangout}</em>
      `;
      if (months.length-4 === index) {
          container.appendChild(card);
      }
    });

  } catch (err) {
    container.innerHTML = `<span style="color:red;">Error: ${err.message}</span>`;
    console.error(err);
  }
}

// Call function
getWeatherMonthly("Cairo");
 document.queryselector(".weather").onclick = (e)=>{
x=document.queryselector("#city_choice").value
   e.preventDefault()
   getWeatherMonthly(x);}

