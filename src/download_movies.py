import os

import pandas as pd
from SPARQLWrapper import JSON, SPARQLWrapper


def run_sparql_query(query):
    """
    Executes a SPARQL query and returns the results.
    """
    endpoint_url = "https://query.wikidata.org/sparql"
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def generate_csv_for_year(year):
    """
    Generates a CSV file containing movie data for a specified year.
    """
    # Update the base query to use the dynamic year filter
    # Generate the CSV file name
    print(f"Downloading year {year}")
    csv_file_name = f"movies_data_{year}_extended.csv"

    # Check if the file already exists
    if os.path.exists(csv_file_name):
        print(f"File already exists: {csv_file_name}, skipping year {year}.")
        return  # Skip processing if file exists

    base_query = f"""
    SELECT ?film ?filmLabel
        (GROUP_CONCAT(DISTINCT ?genreLabel; separator=", ") AS ?genres)
        (GROUP_CONCAT(DISTINCT ?countryLabel; separator=", ") AS ?countries)
        (GROUP_CONCAT(DISTINCT ?directorLabel; separator=", ") AS ?directors)
        (GROUP_CONCAT(DISTINCT ?actorLabel; separator=", ") AS ?actors)
        (GROUP_CONCAT(DISTINCT ?languageLabel; separator=", ") AS ?languages)
        (GROUP_CONCAT(DISTINCT ?topicLabel; separator=", ") AS ?tags)
        ?duration
        (YEAR(?releaseDate) AS ?year)
    WHERE {{
        ?film wdt:P31 wd:Q11424;  # Instance of film
              wdt:P577 ?releaseDate.  # Release date
        FILTER(YEAR(?releaseDate) = {year})  # Dynamically filter by year

        # Get genre
        OPTIONAL {{
            ?film wdt:P136 ?genre.
            ?genre rdfs:label ?genreLabel.
            FILTER(LANG(?genreLabel) = "en")
        }}

        # Get country
        OPTIONAL {{
            ?film wdt:P495 ?country.
            ?country rdfs:label ?countryLabel.
            FILTER(LANG(?countryLabel) = "en")
        }}

        # Get director
        OPTIONAL {{
            ?film wdt:P57 ?director.
            ?director rdfs:label ?directorLabel.
            FILTER(LANG(?directorLabel) = "en")
        }}

        # Get actors
        OPTIONAL {{
            ?film wdt:P161 ?actor.
            ?actor rdfs:label ?actorLabel.
            FILTER(LANG(?actorLabel) = "en")
        }}

        # Get original language
        OPTIONAL {{
            ?film wdt:P364 ?language.
            ?language rdfs:label ?languageLabel.
            FILTER(LANG(?languageLabel) = "en")
        }}

        # Get topics or tags
        OPTIONAL {{
            ?film wdt:P921 ?topic.
            ?topic rdfs:label ?topicLabel.
            FILTER(LANG(?topicLabel) = "en")
        }}

        # Get duration (in minutes)
        OPTIONAL {{
            ?film wdt:P2047 ?duration.
        }}

        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    GROUP BY ?film ?filmLabel ?releaseDate ?duration
    ORDER BY ?year
    """

    # Run the query
    results = run_sparql_query(base_query)

    # Extract the relevant fields from the query results
    films = []
    for result in results["results"]["bindings"]:
        film = {
            "Film": result["filmLabel"]["value"],
            "Genres": result.get("genres", {}).get("value", ""),
            "Countries": result.get("countries", {}).get("value", ""),
            "Directors": result.get("directors", {}).get("value", ""),
            "Actors": result.get("actors", {}).get("value", ""),
            "Languages": result.get("languages", {}).get("value", ""),
            "Tags": result.get("tags", {}).get("value", ""),
            "Duration": result.get("duration", {}).get("value", ""),
            "Year": result.get("year", {}).get("value", ""),
        }
        films.append(film)

    # Convert to DataFrame
    df = pd.DataFrame(films)

    # Save the DataFrame to CSV
    df.to_csv(csv_file_name, index=False)

    print(f"CSV file generated: {csv_file_name}")


# Example usage: Generate CSV for the year 2010
for year in range(1888, 2024):
    generate_csv_for_year(year)
