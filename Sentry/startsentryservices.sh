#!/bin/bash

gnome-terminal --geometry 80x24+0+0 -- sh -c "/home/someuser/projects/sentryscripts/sentryworker.sh; bash"
gnome-terminal --geometry 80x24+1200+0 -- sh -c "/home/someuser/projects/sentryscripts/sentrycron.sh; bash"
gnome-terminal --geometry 80x24+3200+0 --full-screen -- sh -c "/home/someuser/projects/sentryscripts/sentryweb.sh; bash"