# Q & A

## What does?
- Finds and fixes missing tracks (those with an !) in iTunes, using a rough guess based on its old location.

## What need?
- `pip3 install appscript editdistance`

## Does this work?
- It worked on my computer.

## Why do you get the track information from "iTunes Library.xml" instead of querying iTunes (with Applescript)?
- Applescript doesn't returns the old location if the location does not point to a file. I think.

## When will this be updated?
- The next time iTunes fucks up my library.

# TODO
- Finding best matches for tracks with no location
- A confirmation interface/dialog/whatever
  - Show a pretty diff to check if the script fucked up

# References
- https://keystrokecountdown.com/articles/itunes/index.html
