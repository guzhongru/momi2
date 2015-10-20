import pytest
import os, random
import autograd.numpy as np
from autograd import grad

from momi import Demography, simulate_ms, sfs_list_from_ms, sum_sfs_list, unlinked_mle_search
import momi
from test_ms import ms_path

@pytest.mark.parametrize("folded",(True,False))
def test_jointime_inference(folded):
    mu=1e-4
    t0=random.uniform(.25,2.5)
    t1= t0 + random.uniform(.5,5.0)
    num_runs = 10000

    def get_demo(join_time):
        join_time = join_time[0]
        return Demography.from_ms(1e4,"-I 3 1 1 1 -ej $0 1 2 -ej $1 2 3",
                                  join_time, t1)

    true_demo = get_demo([t0])
    sfs = sum_sfs_list(sfs_list_from_ms(simulate_ms(ms_path, true_demo, num_loci=num_runs, mu_per_locus=mu)))
    if folded:
        sfs = momi.util.folded_sfs(sfs, true_demo.n_at_leaves)
    
    print(t0,t1)
    
    x0 = np.array([random.uniform(0,t1)])
    #res = unlinked_mle_search(sfs, get_demo, mu * num_runs, x0, bounds=[(0,t1)], folded=folded)
    res = unlinked_mle_search(sfs, get_demo, None, x0, bounds=[(0,t1)], folded=folded)
    
    print res.jac
    assert abs(res.x - t0) / t0 < .05

@pytest.mark.parametrize("folded",(True,False))
def test_underflow_robustness(folded):
    num_runs = 1000
    mu=1e-3
    def get_demo(t):
        print t
        t0,t1 = t
        return Demography.from_ms(1e4,"-I 3 5 5 5 -ej $0 1 2 -ej $1 2 3", np.exp(t0),np.exp(t0) + np.exp(t1))
    true_x = np.array([np.log(.5),np.log(.2)])
    true_demo = get_demo(true_x)

    sfs = sum_sfs_list(sfs_list_from_ms(simulate_ms(ms_path, true_demo, num_loci=num_runs, mu_per_locus=mu)))
    if folded:
        sfs = momi.util.folded_sfs(sfs, true_demo.n_at_leaves)
    
    optimize_res = unlinked_mle_search(sfs, get_demo, mu * num_runs, np.array([np.log(0.1),np.log(100.0)]), hessp=True, method='newton-cg', folded=folded)
    print optimize_res
    
    inferred_x = optimize_res.x
    error = (true_x - inferred_x) / true_x
    print "# Truth:\n", true_x
    print "# Inferred:\n", inferred_x
    print "# Max Relative Error: %f" % max(abs(error))
    print "# Relative Error:","\n", error

    assert max(abs(error)) < .1
