"""Conditional global value bounds for B7 joint log-interaction model.

Requires positive A/B/exponents, nonpositive GN/GD and positive quality gain
throughout the declared rectangle. Bounds use floating-point safety margins,
not rigorous interval arithmetic. Never reuse for an arbitrary loss family.
"""
import heapq
import math
from q3_quality_cost_geometry import delta_g


def certify(theta,support,budget,context,family,q0=.5,tolerance=1e-7):
    E,A,B,alpha,beta,g0,gn,gd=map(float,theta)
    (nl,nh),(dl,dh),(ql,qh)=support
    if not all(math.isfinite(x) for x in (*theta,budget,context,q0,tolerance)) or min(A,B,alpha,beta,budget,tolerance)<=0:
        raise ValueError('invalid certificate parameters')
    if gn>0 or gd>0 or not ql<=q0<qh<=1:
        raise ValueError('certificate convexity prerequisites not satisfied')
    if min(g0+gn*math.log(n)+gd*math.log(d/100) for n in (nl,nh) for d in (dl,dh))<=0:
        raise ValueError('quality monotonicity not certified')
    c=6e18+2e14*context
    if budget<c*nl*dl:return {'feasible':False,'minimum_cost':c*nl*dl}

    def fixed(cost_q,loss_q):
        h=1e9*delta_g(cost_q,q0,family)
        upper=min(nh,(budget/dl-h)/c)
        if upper<nl:return None
        lo,hi=math.log(nl),math.log(upper)
        def evaluate(x):
            n=math.exp(x);d=min(dh,budget/(c*n+h))
            gain=g0+gn*x+gd*math.log(d/100)
            value=E+A*n**-alpha+B*d**-beta+(1-loss_q)*gain
            dy=0. if budget/(c*n+h)>dh else -c*n/(c*n+h)
            grad=-alpha*A*n**-alpha+(1-loss_q)*gn+dy*(-beta*B*d**-beta+(1-loss_q)*gd)
            return value,grad,n,d
        left,right=lo,hi
        for _ in range(52):
            mid=(left+right)/2
            if evaluate(mid)[1]>0:right=mid
            else:left=mid
        candidates=[lo,hi,(left+right)/2]
        kink=(budget/dh-h)/c
        if nl<kink<upper:candidates.append(math.log(kink))
        x=min(candidates,key=lambda x:evaluate(x)[0])
        value,grad,n,d=evaluate(x)
        # Convex supporting line gives a valid lower bound even at an endpoint.
        lower=value+min(grad*(lo-x),grad*(hi-x))-1e-11*max(1,abs(value))
        return value,lower,n,d

    if fixed(qh,qh) is None:
        left,right=q0,qh
        for _ in range(55):
            mid=(left+right)/2
            if fixed(mid,mid) is None:right=mid
            else:left=mid
        qh=left
    best_q=q0;best=fixed(q0,q0)
    def consider(q):
        nonlocal best,best_q
        candidate=fixed(q,q)
        if candidate[0]<best[0]:best,best_q=candidate,q
    consider(qh)
    heap=[(fixed(q0,qh)[1],q0,qh)];steps=0
    while best[0]-heap[0][0]>tolerance:
        bound,a,b=heapq.heappop(heap);mid=(a+b)/2
        consider(mid)
        for l,r in ((a,mid),(mid,b)):
            heapq.heappush(heap,(fixed(l,r)[1],l,r))
        steps+=1
        if steps>200000:raise RuntimeError('joint certificate iteration limit')
    return {'feasible':True,'global_lower_bound':heap[0][0], 'feasible_upper_bound':best[0],
            'global_gap':best[0]-heap[0][0],'certificate_tolerance':tolerance,'interval_splits':steps,
            'N_params_B':best[2],'D_tokens_B':best[3],'Q_score':best_q}
