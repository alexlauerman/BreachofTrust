This very alpha branch (in development) takes a set amount of samples to eliminate any "noise" in the oracle.  Padding it out to the blocksize to eliminates CBC pading is also needed to be added.

This is test code to exploit the compression attack on SSL that is known as BREACH.  

It currently has limitations due to the nature of the attack (requires target server to support HTTP Compression and you to MITM the connection). It also has limitations due to features that have not been implemented, such as no support for CBC mode SSL.  I am working on a branch that supports varying response lengths and returns the mode.  Please contact me (myname at gmail) if you'd like this.

This isn't the level of quality that I wanted to get this to, but I wanted to check it in and share it before I got pulled away on other projects.

There is a video of this in action here: https://www.youtube.com/watch?v=z_ZnNKyuIpE
