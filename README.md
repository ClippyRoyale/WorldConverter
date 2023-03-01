# Deluxifier
The community-supported MR Deluxe world converter

Source code and documentation copyright (C) 2022–2023 clippy#4722 (AKA WaCopyrightInfringio)
(See https://tinyurl.com/infernopatch for an explanation of my old username.)

# Quick start link: https://replit.com/@WaluigiRoyale/Deluxifier

## What is this?

This is a Python program designed to convert MRoyale Legacy worlds to the updated MRoyale Deluxe format. The lead developers of Deluxe have said they will not officially support Legacy worlds in Deluxe, but the world formats are similar enough that this converter can provide semi-official community support for playing the old worlds in the new game. You can play converted worlds as-is, or use them as a starting point to make a world more consistent with Deluxe's visual style.

## How do I use it?

There are two main ways to run this program:

1. On your computer. The app will run faster and look better but some programming experience is recommended. You’ll need to install Python. If you aren’t allowed to install programs on your computer (e.g. because it’s a school computer), try option 2...
2. Online with Replit. This method is a little clunkier but it’s more beginner-friendly and supports basically any device, including Windows, Mac, Linux, Chromebooks, Android, and iOS. Link: https://replit.com/@WaluigiRoyale/Deluxifier

## ⚠️ WARNING - HEALTH AND SAFETY
Playing converted worlds may get you banned from MR Deluxe! This appears to be a false positive in the game's anticheat. This bug is known to be triggered by converting the Royale City world. It may affect other worlds with vertical scrolling or Remake-only features. I am not responsible if this program lands you in jail!!!

Also: MR Deluxe is in closed alpha. As such, while I am reasonably confident in the stability of the converter at this point, I’m still calling this a public beta. The world format may change at any time. Don't delete your old world files (even after the game is out).

## Other Known Bugs
- MRDX will not load music in converted worlds
- All worlds use the Deluxe obj sheet
- assets.json animations will play at 2× speed since the game is now 60fps

## Troubleshooting

### I can’t get it to run! All I see is a blank screen!

Try clicking “Stop” then clicking “Run” again. If that doesn’t work, clear your cache ( ͡° ͜ʖ ͡°)

### I downloaded the code, and when I run the program, it's in fullscreen!

This is the source code for the Online Version as seen on Replit. Either download the Offline Version on the Discord, or delete the following lines from the source code:

```
# UNCOMMENT THIS LINE ON REPLIT BUILDS OR TO RUN THE APP IN FULLSCREEN
window.attributes('-fullscreen', True)
```
