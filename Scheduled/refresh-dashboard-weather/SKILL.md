---
name: refresh-dashboard-weather
description: Twice daily (6am + 6pm ET): refresh weather block on the attention-today dashboard artifact.
---

Refresh the weather block on the attention-today dashboard artifact for Washington, DC.

Steps:
1. Fetch current conditions via WebFetch from https://api.weather.gov/gridpoints/LWX/96,72/forecast/hourly — take the FIRST period and extract temperature, temperatureUnit, shortForecast, windSpeed, windDirection, probabilityOfPrecipitation.value, relativeHumidity.value, startTime.
2. Fetch the multi-period forecast from https://api.weather.gov/gridpoints/LWX/96,72/forecast — take the first three periods (today, tonight, tomorrow) and extract name, temperature, temperatureUnit, shortForecast, windSpeed, windDirection, probabilityOfPrecipitation.value.
3. Read the artifact at /sessions/upbeat-awesome-hypatia/mnt/.artifacts/attention-today/index.html
4. Replace the JSON inside the <!-- WEATHER_DATA_START --> ... <!-- WEATHER_DATA_END --> markers with a new JSON object of shape:
   {
     "location": "Washington, DC",
     "fetchedAt": "<ISO timestamp now>",
     "now": { temperature, temperatureUnit, shortForecast, windSpeed, windDirection, probabilityOfPrecipitation, relativeHumidity },
     "today": { name, temperature, temperatureUnit, shortForecast, windSpeed, windDirection, probabilityOfPrecipitation },
     "tonight": { name, temperature, temperatureUnit, shortForecast, windSpeed, windDirection, probabilityOfPrecipitation },
     "tomorrow": { name, temperature, temperatureUnit, shortForecast, windSpeed, windDirection, probabilityOfPrecipitation }
   }
5. Use mcp__cowork__update_artifact with id "attention-today" and the full updated HTML; update_summary = "Hourly weather refresh".

Do not change any other part of the artifact. Be quick and silent — no need to summarize the work in chat output.