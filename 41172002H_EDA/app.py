from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
import urllib.parse

app = Flask(__name__)

# — Load & clean data
df = pd.read_csv("PS4_GamesSales.csv", encoding="latin1")
df = df.dropna(subset=["Global", "Year", "Genre"])
df["Global"] = df["Global"].astype(float)
df["Year"] = df["Year"].astype(int)
all_genres = sorted(df["Genre"].unique())

@app.route("/", methods=["GET"])
def index():
    genres    = request.values.getlist("genre")
    year_from = int(request.values.get("year_from", 2013))
    year_to   = int(request.values.get("year_to", 2020))
    page      = int(request.values.get("page", 1))
    picked    = request.values.get("game", "")

    # Filters
    filtered = df[df["Year"].between(year_from, year_to)]
    if genres:
        filtered = filtered[filtered["Genre"].isin(genres)]

    # Pagination
    per_page = 10
    total    = len(filtered)
    pages    = (total + per_page - 1) // per_page
    page     = max(1, min(page, pages))
    start    = (page - 1) * per_page
    page_df  = filtered.iloc[start:start + per_page]

    if picked not in page_df["Game"].values:
        picked = page_df.iloc[0]["Game"] if not page_df.empty else ""

    # Generate links for games
    base_params = [( "year_from", year_from ), ( "year_to", year_to )]
    if genres:
        for g in genres: base_params.append(("genre", g))
    base_params.append(("page", page))
    base_q = urllib.parse.urlencode(base_params, doseq=True)

    games = []
    for _, row in page_df.iterrows():
        q = base_q + "&game=" + urllib.parse.quote(row["Game"], safe="")
        games.append({
            "Game": row["Game"],
            "Year": row["Year"],
            "Genre": row["Genre"],
            "Publisher": row["Publisher"],
            "Global": f"{row['Global']:.2f}",
            "link": "?" + q
        })

    # Pie chart for selected game
    pie_div = ""
    if picked:
        r = df[df["Game"] == picked].iloc[0]
        pie_df = pd.DataFrame({
            "Region": ["North America", "Europe", "Japan", "Rest of World"],
            "Sales": [r["North America"], r["Europe"], r["Japan"], r["Rest of World"]]
        })
        pie = px.pie(pie_df, names="Region", values="Sales", title=f"Regional Sales for {picked}")
        pie.update_traces(textposition='inside', textinfo='percent+label')
        pie_div = pie.to_html(full_html=False)

    # Other charts
    genre_sales = df.groupby("Genre")["Global"].sum().nlargest(10).reset_index()
    genre_div = px.bar(genre_sales, x="Global", y="Genre", orientation="h",
                       title="Top 10 Genres by Global Sales").to_html(full_html=False)

    pub_sales = df.groupby("Publisher")["Global"].sum().nlargest(10).reset_index()
    pub_div = px.bar(pub_sales, x="Global", y="Publisher", orientation="h",
                     title="Top 10 Publishers by Global Sales").to_html(full_html=False)

    yc = df[df["Year"].between(2013, 2017)].groupby("Year")["Game"].count().reset_index(name="Count")
    year_div = px.bar(yc, x="Year", y="Count", title="Games Released per Year (2013–2017)").to_html(full_html=False)

    return render_template("index.html",
        all_genres=all_genres,
        selected_genres=genres,
        year_from=year_from,
        year_to=year_to,
        games=games,
        pie_div=pie_div,
        genre_div=genre_div,
        pub_div=pub_div,
        year_div=year_div,
        picked_game=picked,
        page=page,
        pages=pages
    )

if __name__ == "__main__":
    app.run(debug=True)
