from itertools import product
from math import comb
from random import Random
import unittest

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.polynomial import (
    FormalPowerSeriesMod as FPS, multipoint_evaluation, polynomial_interpolation,
    polynomial_roots, polynomial_shift, polynomial_shift_sampling,
)


def evaluate(coefficients: list[int], x: int, mod: int) -> int:
    result=0
    for value in reversed(coefficients):result=(result*x+value)%mod
    return result


def multiply(a: list[int], b: list[int], mod: int) -> list[int]:
    if not a or not b:return []
    result=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):result[i+j]=(result[i+j]+x*y)%mod
    return result


class PolynomialEvaluationContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod=FPS.get_mod()
        self.transform=ConvolutionMod.get_mod()
        self.threshold=FPS._sparse_threshold
        FPS.set_sparse_threshold(None)

    def tearDown(self) -> None:
        if FPS.get_mod()!=self.mod:FPS.set_mod(self.mod)
        if ConvolutionMod.get_mod()!=self.transform:ConvolutionMod.set_mod(self.transform)
        FPS.set_sparse_threshold(self.threshold)

    def test_evaluation_and_interpolation(self) -> None:
        rng=Random(0)
        for mod in (2,3,5,17,257,998244353,1000000007):
            FPS.set_mod(mod)
            for _ in range(120):
                n=rng.randrange(min(mod,16)+1)
                coefficients=[rng.randrange(-mod,2*mod) for _ in range(n)]
                xs=[x+mod*rng.randrange(-2,3) for x in rng.sample(range(mod),n)]
                ys=[evaluate(coefficients,x,mod) for x in xs]
                original=coefficients[:],xs[:],ys[:]
                self.assertEqual(polynomial_interpolation(xs,ys).coef,[x%mod for x in coefficients])
                self.assertEqual(multipoint_evaluation(FPS(coefficients),xs),ys)
                points=[rng.randrange(-2*mod,2*mod) for _ in range(rng.randrange(20))]
                self.assertEqual(multipoint_evaluation(FPS(coefficients),points),[evaluate(coefficients,x,mod) for x in points])
                self.assertEqual((coefficients,xs,ys),original)
            for xs,ys in (([1],[]),([],[1]),([1,1],[2,2]),([0,mod],[0,1])):
                with self.assertRaises(ValueError):polynomial_interpolation(xs,ys)

    def test_taylor_shift(self) -> None:
        rng=Random(1)
        for mod in (2,3,5,17,998244353,1000000007):
            FPS.set_mod(mod)
            for n in range(26):
                coefficients=[rng.randrange(-mod,mod) for _ in range(n)]
                for c in (0,-1,2,mod+1,10**30):
                    expected=[sum(coefficients[j]*comb(j,i)*pow(c,j-i,mod) for j in range(i,n))%mod for i in range(n)]
                    f=FPS(coefficients)
                    self.assertEqual(polynomial_shift(f,c).coef,expected,(mod,n,c))
                    self.assertEqual(f.coef,coefficients)

    def test_shift_sampling(self) -> None:
        rng=Random(2)
        for mod in (2,3,5,17,97,998244353,1000000007):
            FPS.set_mod(mod)
            for _ in range(200):
                n=rng.randrange(min(mod,15)+1)
                coefficients=[rng.randrange(-mod,mod) for _ in range(n)]
                ys=[evaluate(coefficients,i,mod)+rng.randrange(-2,3)*mod for i in range(n)]
                c=rng.choice([-10**30,-1,0,n,mod-1,mod+1,rng.randrange(100)])
                m=rng.randrange(100)
                before=ys[:]
                self.assertEqual(polynomial_shift_sampling(n,m,ys,c),[evaluate(coefficients,c+i,mod) for i in range(m)],(mod,n,m,c))
                self.assertEqual(ys,before)
            for n,m,ys in ((-1,0,[]),(0,-1,[]),(2,1,[1]),(mod+1,0,[])):
                with self.assertRaises(ValueError):polynomial_shift_sampling(n,m,ys,0)
        FPS.set_mod(3)
        self.assertEqual(polynomial_shift_sampling(2,10000,[0,1],2),[(2+i)%3 for i in range(10000)])
        self.assertEqual(polynomial_shift_sampling(3,10000,[0,1,1],2),[((2+i)%3)**2%3 for i in range(10000)])

    def test_roots_in_small_fields(self) -> None:
        for mod,max_length in ((2,8),(3,5),(5,4)):
            FPS.set_mod(mod)
            for length in range(max_length+1):
                for values in product(range(mod),repeat=length):
                    coefficients=list(values)
                    if not any(coefficients):
                        with self.assertRaises(ValueError):polynomial_roots(FPS(coefficients))
                    else:
                        expected=[x for x in range(mod) if evaluate(coefficients,x,mod)==0]
                        self.assertEqual(polynomial_roots(FPS(coefficients)),expected,(mod,values))
        rng=Random(3)
        FPS.set_mod(17)
        for _ in range(200):
            coefficients=[rng.randrange(-17,34) for _ in range(rng.randrange(1,16))]
            if not any(x%17 for x in coefficients):continue
            self.assertEqual(polynomial_roots(FPS(coefficients)),[x for x in range(17) if evaluate(coefficients,x,17)==0])

    def test_roots_in_large_field(self) -> None:
        rng=Random(4)
        mod=998244353
        FPS.set_mod(mod)
        nonresidue=next(x for x in range(2,100) if pow(x,(mod-1)//2,mod)==mod-1)
        for _ in range(100):
            roots=[rng.randrange(mod) for _ in range(rng.randrange(9))]
            coefficients=[1]
            for root in roots+roots[:3]:coefficients=multiply(coefficients,[-root,1],mod)
            coefficients=multiply(coefficients,[-nonresidue,0,1],mod)
            raw=[x+mod*rng.randrange(-2,3) for x in coefficients]+[mod,0]
            f=FPS(raw)
            self.assertEqual(polynomial_roots(f),sorted(set(roots)))
            self.assertEqual(f.coef,raw)


if __name__=='__main__':
    unittest.main()
