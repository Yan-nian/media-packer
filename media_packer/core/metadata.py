"""Metadata management for TV shows and movies"""
import logging
from typing import Optional, List, Dict, Any
from tmdbv3api import TMDb, TV, Movie, Search
from ..models import SeriesInfo, MovieInfo, EpisodeInfo, MediaType
import requests

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manages metadata retrieval from TMDB and other sources"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.tmdb = TMDb()
        if api_key:
            self.tmdb.api_key = api_key
        self.tv = TV()
        self.movie = Movie()
        self.search = Search()
    
    def search_series(self, title: str, year: Optional[int] = None) -> List[SeriesInfo]:
        """Search for TV series by title"""
        if not self.tmdb.api_key:
            logger.warning("TMDB API key not set, skipping metadata search")
            return []
        
        try:
            results = self.search.tv(query=title, first_air_date_year=year)
            series_list = []
            
            for result in results[:5]:  # Limit to top 5 results
                series_info = SeriesInfo(
                    title=result.name,
                    year=int(result.first_air_date[:4]) if result.first_air_date else None,
                    tmdb_id=result.id,
                    overview=result.overview,
                    poster_path=result.poster_path,
                    backdrop_path=result.backdrop_path
                )
                series_list.append(series_info)
            
            return series_list
        except Exception as e:
            logger.error(f"Error searching for series '{title}': {e}")
            return []
    
    def search_movie(self, title: str, year: Optional[int] = None) -> List[MovieInfo]:
        """Search for movies by title"""
        if not self.tmdb.api_key:
            logger.warning("TMDB API key not set, skipping metadata search")
            return []
        
        try:
            results = self.search.movie(query=title, year=year)
            movie_list = []
            
            for result in results[:5]:  # Limit to top 5 results
                movie_info = MovieInfo(
                    title=result.title,
                    year=int(result.release_date[:4]) if result.release_date else None,
                    tmdb_id=result.id,
                    overview=result.overview,
                    poster_path=result.poster_path,
                    backdrop_path=result.backdrop_path
                )
                movie_list.append(movie_info)
            
            return movie_list
        except Exception as e:
            logger.error(f"Error searching for movie '{title}': {e}")
            return []
    
    def get_series_details(self, tmdb_id: int) -> Optional[SeriesInfo]:
        """Get detailed information for a TV series"""
        if not self.tmdb.api_key:
            return None
        
        try:
            details = self.tv.details(tmdb_id)
            
            return SeriesInfo(
                title=details.name,
                year=int(details.first_air_date[:4]) if details.first_air_date else None,
                tmdb_id=details.id,
                overview=details.overview,
                genres=[genre['name'] for genre in details.genres],
                network=details.networks[0]['name'] if details.networks else None,
                status=details.status,
                poster_path=details.poster_path,
                backdrop_path=details.backdrop_path
            )
        except Exception as e:
            logger.error(f"Error getting series details for ID {tmdb_id}: {e}")
            return None
    
    def get_movie_details(self, tmdb_id: int) -> Optional[MovieInfo]:
        """Get detailed information for a movie"""
        if not self.tmdb.api_key:
            return None
        
        try:
            details = self.movie.details(tmdb_id)
            
            # Get director from crew
            director = None
            if hasattr(details, 'credits') and details.credits:
                crew = details.credits.get('crew', [])
                for person in crew:
                    if person.get('job') == 'Director':
                        director = person.get('name')
                        break
            
            return MovieInfo(
                title=details.title,
                year=int(details.release_date[:4]) if details.release_date else None,
                tmdb_id=details.id,
                imdb_id=details.imdb_id,
                overview=details.overview,
                genres=[genre['name'] for genre in details.genres],
                director=director,
                runtime=details.runtime,
                poster_path=details.poster_path,
                backdrop_path=details.backdrop_path
            )
        except Exception as e:
            logger.error(f"Error getting movie details for ID {tmdb_id}: {e}")
            return None
    
    def get_episode_details(self, tmdb_id: int, season: int, episode: int) -> Optional[EpisodeInfo]:
        """Get detailed information for a specific episode"""
        if not self.tmdb.api_key:
            return None
        
        try:
            episode_details = self.tv.episode_details(tmdb_id, season, episode)
            
            return EpisodeInfo(
                season=season,
                episode=episode,
                title=episode_details.name,
                overview=episode_details.overview,
                air_date=episode_details.air_date
            )
        except Exception as e:
            logger.error(f"Error getting episode details for ID {tmdb_id} S{season}E{episode}: {e}")
            return None
    
    def download_image(self, image_path: str, output_path: str) -> bool:
        """Download poster or backdrop image from TMDB"""
        if not image_path:
            return False
        
        try:
            base_url = "https://image.tmdb.org/t/p/original"
            full_url = f"{base_url}{image_path}"
            
            response = requests.get(full_url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded image: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading image {image_path}: {e}")
            return False
    
    def auto_match_metadata(
        self, 
        title: str, 
        year: Optional[int], 
        media_type: MediaType
    ) -> Optional[Dict[str, Any]]:
        """Automatically match and return best metadata"""
        if media_type == MediaType.TV_SHOW:
            results = self.search_series(title, year)
            if results:
                # Get detailed info for best match
                best_match = results[0]
                detailed_info = self.get_series_details(best_match.tmdb_id)
                return {
                    'type': 'series',
                    'info': detailed_info,
                    'confidence': self._calculate_match_confidence(title, year, best_match.title, best_match.year)
                }
        elif media_type == MediaType.MOVIE:
            results = self.search_movie(title, year)
            if results:
                # Get detailed info for best match
                best_match = results[0]
                detailed_info = self.get_movie_details(best_match.tmdb_id)
                return {
                    'type': 'movie',
                    'info': detailed_info,
                    'confidence': self._calculate_match_confidence(title, year, best_match.title, best_match.year)
                }
        
        return None
    
    def _calculate_match_confidence(
        self, 
        search_title: str, 
        search_year: Optional[int],
        result_title: str, 
        result_year: Optional[int]
    ) -> float:
        """Calculate confidence score for metadata match"""
        confidence = 0.0
        
        # Title similarity (basic)
        if search_title.lower() == result_title.lower():
            confidence += 0.7
        elif search_title.lower() in result_title.lower() or result_title.lower() in search_title.lower():
            confidence += 0.5
        
        # Year matching
        if search_year and result_year:
            if search_year == result_year:
                confidence += 0.3
            elif abs(search_year - result_year) <= 1:
                confidence += 0.2
        
        return min(confidence, 1.0)


class NFOGenerator:
    """Generates NFO files for media centers like Kodi/Plex"""
    
    @staticmethod
    def generate_movie_nfo(movie_info: MovieInfo) -> str:
        """Generate NFO content for a movie"""
        nfo_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
    <title>{movie_info.title}</title>
    <year>{movie_info.year or ''}</year>
    <plot>{movie_info.overview or ''}</plot>
    <runtime>{movie_info.runtime or ''}</runtime>
    <director>{movie_info.director or ''}</director>
    <tmdbid>{movie_info.tmdb_id or ''}</tmdbid>
    <imdbid>{movie_info.imdb_id or ''}</imdbid>
"""
        
        for genre in movie_info.genres:
            nfo_content += f"    <genre>{genre}</genre>\n"
        
        if movie_info.poster_path:
            nfo_content += f"    <thumb>https://image.tmdb.org/t/p/original{movie_info.poster_path}</thumb>\n"
        
        nfo_content += "</movie>"
        return nfo_content
    
    @staticmethod
    def generate_tvshow_nfo(series_info: SeriesInfo) -> str:
        """Generate NFO content for a TV show"""
        nfo_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<tvshow>
    <title>{series_info.title}</title>
    <year>{series_info.year or ''}</year>
    <plot>{series_info.overview or ''}</plot>
    <status>{series_info.status or ''}</status>
    <network>{series_info.network or ''}</network>
    <tmdbid>{series_info.tmdb_id or ''}</tmdbid>
"""
        
        for genre in series_info.genres:
            nfo_content += f"    <genre>{genre}</genre>\n"
        
        if series_info.poster_path:
            nfo_content += f"    <thumb>https://image.tmdb.org/t/p/original{series_info.poster_path}</thumb>\n"
        
        nfo_content += "</tvshow>"
        return nfo_content
    
    @staticmethod
    def generate_episode_nfo(episode_info: EpisodeInfo, series_info: SeriesInfo) -> str:
        """Generate NFO content for an episode"""
        nfo_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<episodedetails>
    <title>{episode_info.title or ''}</title>
    <season>{episode_info.season}</season>
    <episode>{episode_info.episode}</episode>
    <plot>{episode_info.overview or ''}</plot>
    <aired>{episode_info.air_date or ''}</aired>
    <showtitle>{series_info.title}</showtitle>
</episodedetails>"""
        return nfo_content