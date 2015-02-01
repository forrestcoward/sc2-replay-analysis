import Orange
import random

def test_random_forest_feature_strength(data):
    measure = Orange.ensemble.forest.ScoreFeature(trees=100)
    print "Feature ranking:"
    for attribute in data.domain.attributes:
        print "%15s: %6.2f" % (attribute.name, measure(attribute, data))    

def test_random_forests(data, file):   
    for num_attributes in range(1, 10, 1):
        print num_attributes, 'attributes'
        print

        for num_trees in range(10, 251, 25):
            print num_trees, 'trees'
            
            # TreeLearner uses GiniRatio by default (Orange documentation is incorrect). 
            tree = Orange.classification.tree.TreeLearner(min_instances=7, measure=Orange.feature.scoring.Gini(), name='tree')
            # SimpleTreeLearner uses GainRatio by default as well. 
            simple_tree = Orange.classification.tree.SimpleTreeLearner(min_instances=7)
            
            forest = Orange.ensemble.forest.RandomForestLearner(trees=num_trees, attributes=num_attributes, base_learner=simple_tree, name="forest")   
            learners = [forest]
            results = Orange.evaluation.testing.cross_validation(learners, data, folds=5)

            CA = print_cv_results(results)
            file.write(str(num_attributes) + '\t')
            file.write(str(num_trees) + '\t')
            file.write(str(CA))
            file.write('\n')
            
def test_decision_trees(data, file):
    for depth in range(4, 5, 1):
        print 'depth', depth
        metrics = [Orange.feature.scoring.InfoGain(), Orange.feature.scoring.Gini(), Orange.feature.scoring.GainRatio()]
        for metric in metrics:
            print 'metric', metric
            tree = Orange.classification.tree.TreeLearner(min_instances=7,  m_pruning=3, min_subset=7, max_majority=95, same_majority_pruning=True, max_depth=depth, measure=metric)
            learners = [tree]
            results = Orange.evaluation.testing.cross_validation(learners, data, folds=5)   
            CA = print_cv_results(results)
            file.write(str(depth) + '\t')
            metric_str = str(metric)
            metric_name = metric_str.split(' ')[-1]
            file.write(metric_name + '\t')
            file.write(str(CA))
            file.write('\n')
            
def print_cv_results(results):                   
    correct = 0
    within_one = 0
    within_two = 0
            
    for result in results.results:
        actual = result.actualClass
        prediction = int(result.classes[0])
    
        if actual == prediction:
            correct += 1
            within_one += 1
            within_two += 1
        elif actual == prediction + 1 or actual == prediction - 1:
            within_one += 1
            within_two += 1
        elif actual == prediction + 2 or actual == prediction - 2:
            within_two += 1
        
    size = float(len(results.results))
    print correct / size
    print within_one / size
    # print within_two / size
    print            
    return correct/size

def main():
    dt = open('decision_trees.tab', 'w')
    forest = open('random_forests.tab', 'w')
    data = Orange.data.Table("data.test.tab")
    #test_random_forest_feature_strength(data)
    #test_random_forests(data, forest)
    test_decision_trees(data, dt)
              
if __name__ == '__main__':
    main()        