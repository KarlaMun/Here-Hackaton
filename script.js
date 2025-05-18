let map;

function initMap() {
    const map = new google.maps.Map(document.getElementById("map"), {
      center: { lat: 19.4326, lng: -99.1332 },

  
      zoom: 19,
      mapTypeId: "satellite",
    });

  }