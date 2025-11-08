# Intro

This is the source code of my website https://theorem-marketplace.com. It was initially private, but now I've decided to make it public. 

The project is somewhat complex and juggles five different docker containers. In an ideal world, I'd make you a neat docker compose file to coordinate them. In the real world... Well, I didn't. If you find this repo useful / wish to reproduce this, I'll try to make this repo slightly friendlier for first time use.

The containers required are:
· theorem-marketplace (this repo, described in the dockerfile) — the web site itself, runs on port 8000.
· a chainlink node. you can read how to start one [here](https://docs.chain.link/chainlink-nodes/v1/running-a-chainlink-node).
· a postgres container required by the chainlink node as described 
· another postgres container to store information about theorems and bounties. (this should really be two databases in the same container, but fixing it requires some slight chainlink messing around, so i haven't gotten to it yet.)
· a safe-verity-adapter container from [a neighboring repo](https://github.com/wadimiusz/safe-verify-adapter/). this will actually be the API that chainlink uses to check if a given proof is valid.

Even aside from orchestrating the docker containers, all this requires some manual shit. Please ask me any questions, or feel free to build upon my work.