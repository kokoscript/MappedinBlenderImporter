# Mappedin Embed Blender Importer
A basic importer for JSON-based geometry data from Mappedin embeds.

## Features
Supported:
 - Basic geometry
 - Holes
 - Materials (color/opacity; use attribute coloring to view)
 - Labels (with some position inaccuracy)

Unsupported:
 - Any location/level information (e.g. map groups)
 - Venue information (including venue labels)
 - Path nodes
 - External images

Essentially, anything outside the geometry JSON is unsupported. I don't plan on adding support for any of it, either.

## Why?
The mall I grew up visiting was set to close soon. In the process of saving bits and pieces of info before it would all inevitably become lost, I ended up archiving their interactive map. Some friends and I were floating around the idea of recreating the mall as a virtual hangout space for something like VRChat, and I thought the map would make for good reference material in the event we decide to go through with the idea. The data looked simple enough, so I wrote this importer.

## Sourcing data
This is left as an exercise to the reader. As a hint, use the network tab on your browser's devtools.

Note that getting the required geometry data doesn't seem to be possible with newer versions of the embed. I tried repeating my process with another (non-dead) mall to get more testing data, but wasn't successful. Dying malls and unmaintained websites go hand-in-hand, so that's probably why I was successful with the mall I was archiving.
