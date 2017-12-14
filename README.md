# anki-local-time-change
Allow to synchronize with a clock ahead or late by a constant time

Anki's synchronization require that your time is synchronized with ankiweb's time. The error should be least than 5 minutes. If, for some reason, your computer is late or ahead by a fixed time, this add-on allows you to synchronize.

By default, this add-on is configured to work for computers five minutes ahead (because this was requested in https://www.reddit.com/r/Anki/comments/7jooar/is_it_possible_to_use_ankiankidroid_with_a_clock/ ).

#Configuration
Tools>add-ons>time_move>Edit...
In the first few lines, replace the number by the actual number of seconds, minutes, hours, days and weeks by week your computer is ahead. If your computer is Late, switch
"ahead = True"
to
"ahead = False"




