# sc2-replay-analysis
Starcraft 2 replay parsing, storage, and analysis

This is some work I did for my machine learning class back when I was in college. There are a few pieces:

1) A Starcraft 2 replay parser using the sc2reader project. I use MongoDB to store replay statistics.

2) Queries against MongoDB to get very specific game statistics. For example, you could ask “In master league games, what percentage of games does terran win versus zerg when the terran player has 40 SCVs by the 6th minute“? To my knowledge, nobody in the starcraft community has tried to answer these types of questions.

3) A battle net league scrapper for retrieving the highest league level a player has received.

4) A machine learning component that uses decision trees and random forests to determine the most useful replay statistics for predicting a players league given a replay. It turns out that actions per minute (APM) and spending quotient (SQ) are by far the best predictors of a player’s skill. I wrote a paper for my machine learning class that I included.
