import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from rdflib import Graph, URIRef
from utils import ordered_leg_names
from rdflib.plugins.sparql import prepareQuery
from rdflib.namespace import FOAF, XSD, RDF, DC, RDFS, OWL
from datetime import datetime

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = "Helvetica"


stats = pd.read_csv("stats.csv", encoding="utf-8")

dataset = Graph()

dataset.parse(os.path.join("tagging_modules/rdf/", "legislatura.rdf"), format="nt")

starts = []
ends = []

for leg in ordered_leg_names:
    query = prepareQuery(
        f"""
            SELECT ?start ?end
            WHERE {{
            <http://dati.camera.it/ocd/legislatura.rdf/{leg}> <http://purl.org/dc/elements/1.1/date> ?dates .
            BIND(xsd:integer(strbefore(?dates, "-")) AS ?start) .
            BIND(xsd:integer(strafter(?dates, "-")) AS ?end) .
            }}
        """,
        initNs={"ocd": URIRef("http://dati.camera.it/ocd/")},
    )

    result = dataset.query(query)

    for row in result:
        print("ound" + leg)
        start = row.start
        end = row.end

        starts.append(start)
        ends.append(end)

stats["start"] = starts
stats["end"] = ends

# convert yyyymmdd to datetime

# TypeError: Expected unicode, got Literal


stats["start"] = stats["start"].apply(lambda x: datetime.strptime(str(x), "%Y%m%d"))
stats["end"] = stats["end"].apply(lambda x: datetime.strptime(str(x), "%Y%m%d"))
stats["span"] = (stats["end"] - stats["start"]).dt.days
# convert token_num to millions log
stats["token_num"] = stats["token_num"] / 1000000
# order the palette based on token_num
stats = stats.sort_values(by=["token_num"])
color_palette = sns.color_palette("magma", len(stats))
stats["color"] = color_palette
stats = stats.sort_values(by=["start"])
# Create a diverging color palette (e.g., using RdBu_r)


# plot using time span as width of the bars

# Create a figure and axis
fig, ax = plt.subplots(figsize=(12, 7))

# Loop through the time spans and create bars with varying widths
for index, row in stats.iterrows():
    value = row.token_num

    # color the bar based on the number of tokens
    ax.bar(row.start, value, width=row.span, align="edge", color=row.color)


# Add labels and legend
ax.set_xlabel("Time")
ax.set_ylabel("Number of tokens (millions)")
ax.set_title("Number of tokens per legislature")

# Display the plot
plt.tight_layout()
fig.savefig("tokens_per_leg.png", dpi=200)
