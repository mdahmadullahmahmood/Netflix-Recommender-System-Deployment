// Refactored version of the original movie recommendation client JS
// Major changes:
// - Modern JavaScript (ES6+)
// - Use of async/await instead of synchronous AJAX
// - Better error handling and code structure
// - API key is assumed to be securely handled server-side

$(function () {
  const source = document.getElementById('autoComplete');
  source.addEventListener('input', (e) => {
    $('.movie-button').attr('disabled', e.target.value === '');
  });

  $('.movie-button').on('click', async function () {
    const title = $('.movie').val();
    if (!title) {
      $('.results').hide();
      $('.fail').show();
    } else {
      await loadDetails(title);
    }
  });
});

function recommendcard(e) {
  const title = e.getAttribute('title');
  loadDetails(title);
}

async function loadDetails(title) {
  try {
    const response = await fetch(`/search_movie?title=${encodeURIComponent(title)}`);
    const movie = await response.json();

    if (!movie.results || movie.results.length < 1) {
      $('.fail').show();
      $('.results').hide();
      $("#loader").delay(500).fadeOut();
    } else {
      $('#loader').fadeIn();
      $('.fail').hide();
      $('.results').delay(1000).show();

      const movie_id = movie.results[0].id;
      const movie_title = movie.results[0].original_title;
      await fetchRecommendations(movie_title, movie_id);
    }
  } catch (error) {
    alert('Invalid Request');
    $("#loader").delay(500).fadeOut();
  }
}

async function fetchRecommendations(movie_title, movie_id) {
  try {
    const response = await fetch('/similarity', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: movie_title }),
    });
    const recsText = await response.text();

    if (recsText.includes("not in our database")) {
      $('.fail').show();
      $('.results').hide();
      $("#loader").delay(500).fadeOut();
    } else {
      $('.fail').hide();
      $('.results').show();
      const rec_movies = recsText.split('---');
      await fetchMovieDetails(movie_id, rec_movies, movie_title);
    }
  } catch (error) {
    alert('Error fetching recommendations');
    $("#loader").delay(500).fadeOut();
  }
}

async function fetchMovieDetails(movie_id, rec_movies, movie_title) {
  try {
    const response = await fetch(`/movie_details?id=${movie_id}`);
    const details = await response.json();

    const posters = await getMoviePosters(rec_movies);
    const cast = await getMovieCast(movie_id);
    const castDetails = await getIndividualCast(cast.cast_ids);

    const data = {
      title: movie_title,
      cast_ids: JSON.stringify(cast.cast_ids),
      cast_names: JSON.stringify(cast.cast_names),
      cast_chars: JSON.stringify(cast.cast_chars),
      cast_profiles: JSON.stringify(cast.cast_profiles),
      cast_bdays: JSON.stringify(castDetails.cast_bdays),
      cast_bios: JSON.stringify(castDetails.cast_bios),
      cast_places: JSON.stringify(castDetails.cast_places),
      imdb_id: details.imdb_id,
      poster: `https://image.tmdb.org/t/p/original${details.poster_path}`,
      genres: details.genres.map(g => g.name).join(', '),
      overview: details.overview,
      rating: details.vote_average,
      vote_count: details.vote_count.toLocaleString(),
      release_date: new Date(details.release_date).toDateString().split(' ').slice(1).join(' '),
      runtime: formatRuntime(details.runtime),
      status: details.status,
      rec_movies: JSON.stringify(rec_movies),
      rec_posters: JSON.stringify(posters),
    };

    const recommendResponse = await fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const html = await recommendResponse.text();
    $('.results').html(html);
    $('#autoComplete').val('');
    $(window).scrollTop(0);
    $('#loader').delay(500).fadeOut();
  } catch (error) {
    alert('Error loading movie details');
    $('#loader').delay(500).fadeOut();
  }
}

function formatRuntime(runtime) {
  if (!runtime) return 'N/A';
  const hours = Math.floor(runtime / 60);
  const mins = runtime % 60;
  return mins ? `${hours} hour(s) ${mins} min(s)` : `${hours} hour(s)`;
}

async function getMovieCast(movie_id) {
  const response = await fetch(`/movie_cast?id=${movie_id}`);
  return await response.json();
}

async function getIndividualCast(cast_ids) {
  const bdays = [], bios = [], places = [];
  for (const id of cast_ids) {
    const res = await fetch(`/person?id=${id}`);
    const data = await res.json();
    bdays.push(new Date(data.birthday).toDateString().split(' ').slice(1).join(' '));
    bios.push(data.biography);
    places.push(data.place_of_birth);
  }
  return { cast_bdays: bdays, cast_bios: bios, cast_places: places };
}

async function getMoviePosters(movies) {
  const posters = [];
  for (const movie of movies) {
    const res = await fetch(`/poster?title=${encodeURIComponent(movie)}`);
    const data = await res.json();
    if (data.results && data.results.length > 0) {
      posters.push(`https://image.tmdb.org/t/p/original${data.results[0].poster_path}`);
    } else {
      posters.push(''); // fallback if not found
    }
  }
  return posters;
}
