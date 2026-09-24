from math import factorial
from random import Random
import unittest
from unittest.mock import patch

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.polynomial import (
    FormalPowerSeriesMod as FPS, polynomial_add, polynomial_sub, polynomial_mul_naive,
    polynomial_divmod_naive, polynomial_trim, polynomial_normalize_monic, polynomial_is_zero,
)


def multiply(a: list[int], b: list[int], mod: int, length: int | None = None) -> list[int]:
    size = max(0, len(a) + len(b) - 1) if a and b else 0
    result = [0] * (size if length is None else length)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if i+j < len(result): result[i+j] = (result[i+j] + x*y) % mod
    return result


def trim(a: list[int], mod: int) -> list[int]:
    a = [x % mod for x in a]
    while a and not a[-1]: a.pop()
    return a


def divide(a: list[int], b: list[int], mod: int) -> tuple[list[int], list[int]]:
    a, b = trim(a, mod), trim(b, mod)
    if not b: raise ZeroDivisionError
    quotient = [0] * max(0, len(a) - len(b) + 1)
    for degree in range(len(quotient)-1, -1, -1):
        c = a[degree + len(b) - 1] * pow(b[-1], -1, mod) % mod
        quotient[degree] = c
        for j, x in enumerate(b): a[degree+j] = (a[degree+j] - c*x) % mod
    return trim(quotient, mod), trim(a, mod)


class FPSContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = FPS.get_mod()
        self.transform = ConvolutionMod.get_mod()
        self.threshold = FPS._sparse_threshold

    def tearDown(self) -> None:
        if FPS.get_mod() != self.mod: FPS.set_mod(self.mod)
        if ConvolutionMod.get_mod() != self.transform: ConvolutionMod.set_mod(self.transform)
        FPS.set_sparse_threshold(self.threshold)

    def test_arithmetic_and_division(self) -> None:
        rng = Random(0)
        for mod in (2, 3, 17, 998244353, 1000000007):
            FPS.set_mod(mod)
            for threshold in (None, 100):
                FPS.set_sparse_threshold(threshold)
                for _ in range(150):
                    a = [rng.randrange(-2*mod, 2*mod) for _ in range(rng.randrange(12))]
                    b = [rng.randrange(-2*mod, 2*mod) for _ in range(rng.randrange(12))]
                    if rng.randrange(3) == 0: b += [mod, 0, -mod]
                    f, g = FPS(a), FPS(b)
                    self.assertEqual((-f).coef, [-x % mod for x in a])
                    length = max(len(a), len(b))
                    self.assertEqual((f+g).coef, [((a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0)) % mod for i in range(length)])
                    self.assertEqual((f-g).coef, [((a[i] if i<len(a) else 0)-(b[i] if i<len(b) else 0)) % mod for i in range(length)])
                    self.assertEqual((f*g).coef, multiply(a,b,mod))
                    if trim(b,mod):
                        q,r = divide(a,b,mod)
                        self.assertEqual((f//g).coef, q)
                        self.assertEqual((f%g).coef, r)
                        actual_q,actual_r=f.divmod_poly(g)
                        self.assertEqual((actual_q.coef,actual_r.coef),(q,r))
                    else:
                        for op in (lambda:f//g,lambda:f%g,lambda:f.divmod_poly(g)):
                            with self.assertRaises(ZeroDivisionError): op()
                    scalar = rng.randrange(1,mod)
                    self.assertEqual((f/scalar).coef, [x*pow(scalar,-1,mod)%mod for x in a])
                    self.assertEqual((f%scalar).coef,[0])
                    for zero in (0,mod,-mod):
                        for op in (lambda:f/zero,lambda:f//zero,lambda:f%zero):
                            with self.assertRaises(ZeroDivisionError):op()
                    self.assertEqual(f.coef,a)
                    self.assertEqual(g.coef,b)
        # divmod must not recompute the quotient to obtain the remainder.
        FPS.set_mod(998244353)
        FPS.set_sparse_threshold(None)
        original = FPS._floordiv
        calls: list[int] = []
        def counted(f: FPS, g: FPS) -> FPS:
            calls.append(1)
            return original(f,g)
        with patch.object(FPS, '_floordiv', counted):
            FPS([1,2,3,4]).divmod_poly(FPS([1,2]))
        self.assertEqual(len(calls),1)

    def test_series_inverse_and_quotient(self) -> None:
        rng = Random(1)
        for mod in (2,3,17,998244353,1000000007):
            FPS.set_mod(mod)
            for threshold in (None,100):
                FPS.set_sparse_threshold(threshold)
                for _ in range(100):
                    n = rng.randrange(1,18)
                    a = [rng.randrange(1,mod)] + [rng.randrange(-mod,2*mod) for _ in range(n-1)]
                    b = [rng.randrange(-mod,2*mod) for _ in range(rng.randrange(18))]
                    inverse=(~FPS(a)).coef
                    self.assertEqual(len(inverse),n)
                    self.assertEqual(multiply(a,inverse,mod,n), [1]+[0]*(n-1))
                    quotient=(FPS(b)/FPS(a)).coef
                    size=max(n,len(b))
                    self.assertEqual(multiply(quotient,a,mod,size),[x%mod for x in b]+[0]*(size-len(b)))
                    reflected=(3/FPS(a)).coef
                    self.assertEqual(multiply(reflected,a,mod,n),[3%mod]+[0]*(n-1))
                for a in ([],[0],[mod],[-mod,1]):
                    with self.assertRaises(ZeroDivisionError): ~FPS(a)
                    with self.assertRaises(ZeroDivisionError): FPS([1])/FPS(a)

    def test_log_exp_integral(self) -> None:
        rng=Random(2)
        for mod in (2,3,5,17,998244353,1000000007):
            FPS.set_mod(mod)
            for threshold in (None,100):
                FPS.set_sparse_threshold(threshold)
                for n in range(min(mod,16)+1):
                    a=[0]+[rng.randrange(-mod,mod) for _ in range(n-1)] if n else []
                    expected_exp=[1]+[0]*(n-1) if n else []
                    expected_log=[0]*n
                    power=[1]+[0]*(n-1) if n else []
                    for k in range(1,n):
                        power=multiply(power,a,mod,n)
                        for i,x in enumerate(power):
                            expected_exp[i]=(expected_exp[i]+x*pow(factorial(k),-1,mod))%mod
                            expected_log[i]=(expected_log[i]+x*pow(k,-1,mod)*(-1)**(k+1))%mod
                    f=FPS(a)
                    if n: f[0]=mod
                    self.assertEqual(f.exp().coef,expected_exp,(mod,threshold,n))
                    if n: f[0]=mod+1
                    self.assertEqual(f.log().coef,expected_log,(mod,threshold,n))
                    values=[rng.randrange(-mod,mod) for _ in range(n)]
                    f=FPS(values)
                    derivative=[(i+1)*values[i+1]%mod for i in range(max(0,n-1))]+([0] if n else [])
                    integral=[0]+[values[i-1]*pow(i,-1,mod)%mod for i in range(1,n)] if n else []
                    self.assertEqual(f.derivative().coef,derivative)
                    self.assertEqual(f.integral().coef,integral)
                with self.assertRaises(ValueError): FPS([2]).log()
                with self.assertRaises(ValueError): FPS([1]).exp()
                if mod < 100:
                    for op in (lambda:FPS([0]*(mod+1)).integral(),lambda:FPS([1]+[0]*mod).log(),lambda:FPS([0]*(mod+1)).exp()):
                        with self.assertRaises(ValueError):op()

    def test_integer_powers(self) -> None:
        rng=Random(3)
        for mod in (2,3,17,998244353):
            FPS.set_mod(mod)
            for threshold in (None,100):
                FPS.set_sparse_threshold(threshold)
                for _ in range(180):
                    n=rng.randrange(20)
                    a=[rng.randrange(-mod,mod) for _ in range(n)]
                    if n and rng.randrange(2):
                        for i in range(rng.randrange(n)):a[i]=mod
                    k=rng.randrange(10)
                    expected=[1]+[0]*(n-1) if n else []
                    for _ in range(k):expected=multiply(expected,a,mod,n)
                    self.assertEqual((FPS(a)**k).coef,expected,(mod,threshold,a,k))
                with self.assertRaises(ValueError):FPS([])**-1
                self.assertEqual((FPS([0]*100+[1])**(10**30)).coef,[0]*101)

    def test_square_roots(self) -> None:
        rng=Random(4)
        for mod in (2,3,17,998244353):
            FPS.set_mod(mod)
            for threshold in (None,100):
                FPS.set_sparse_threshold(threshold)
                for _ in range(150):
                    n=rng.randrange(20)
                    root=[rng.randrange(mod) for _ in range(n)]
                    a=multiply(root,root,mod,n)
                    raw=[x+mod*rng.randrange(-2,3) for x in a]
                    actual=FPS(raw).sqrt().coef
                    self.assertEqual(len(actual),n)
                    self.assertEqual(multiply(actual,actual,mod,n),a,(mod,raw,actual))
                with self.assertRaises(ValueError):FPS([0,1]).sqrt()
                if mod>2:
                    nonresidue=next(x for x in range(2,mod) if pow(x,(mod-1)//2,mod)==mod-1)
                    with self.assertRaises(ValueError):FPS([nonresidue]).sqrt()

    def test_representation_and_bounds(self) -> None:
        FPS.set_mod(17)
        f=FPS([17,1,-17,34])
        self.assertEqual(f.nzcount(),1)
        self.assertEqual(f.degree(),1)
        self.assertFalse(f.is_zero())
        self.assertTrue(FPS([17,-17]).is_zero())
        self.assertEqual(f.trimmed().coef,[17,1])
        self.assertEqual(f.coef,[17,1,-17,34])
        f.shrink()
        self.assertEqual(f.coef,[17,1])
        self.assertEqual(f.resize(0).coef,[])
        self.assertEqual(f.resize(4).coef,[17,1,0,0])
        self.assertEqual(f.div_xk(1).coef,[1])
        self.assertEqual(f.div_xk(10).coef,[])
        for fn in (f.resize,f.div_xk):
            with self.assertRaises(ValueError):fn(-1)
        previous=FPS._sparse_threshold
        with self.assertRaises(ValueError):FPS.set_sparse_threshold(-1)
        self.assertEqual(FPS._sparse_threshold,previous)
        FPS.set_mod(998244353)
        self.assertEqual(FPS([998244353, 1-998244353, -1, 0]).compositional_inverse().coef, [0,1,1,2])

    def test_low_level_polynomials(self) -> None:
        rng=Random(5)
        for mod in (1,2,3,9,17):
            for _ in range(100):
                a=[rng.randrange(-20,20) for _ in range(rng.randrange(10))]
                b=[rng.randrange(-20,20) for _ in range(rng.randrange(10))]
                for wrap in (lambda x:x,FPS):
                    self.assertEqual(polynomial_trim(wrap(a),mod),trim(a,mod) or [0])
                    self.assertEqual(polynomial_is_zero(wrap(a),mod),not trim(a,mod))
                    length=max(len(a),len(b))
                    plus=[(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0) for i in range(length)]
                    minus=[(a[i] if i<len(a) else 0)-(b[i] if i<len(b) else 0) for i in range(length)]
                    self.assertEqual(polynomial_add(wrap(a),wrap(b),mod),trim(plus,mod) or [0])
                    self.assertEqual(polynomial_sub(wrap(a),wrap(b),mod),trim(minus,mod) or [0])
                    self.assertEqual(polynomial_mul_naive(wrap(a),wrap(b),mod),trim(multiply(a,b,mod),mod) or [0])
                if trim(b,mod) and mod !=9:
                    q,r=divide(a,b,mod)
                    self.assertEqual(polynomial_divmod_naive(a,b,mod),(q or [0],r or [0]))
                    normalized=polynomial_normalize_monic(b,mod)
                    self.assertEqual(normalized[-1],1)
                    self.assertEqual(normalized,[x*pow(trim(b,mod)[-1],-1,mod)%mod for x in trim(b,mod)])
        for mod in (0,-1):
            for fn in (lambda:polynomial_trim([],mod),lambda:polynomial_normalize_monic([],mod),lambda:polynomial_add([],[],mod),lambda:polynomial_sub([],[],mod),lambda:polynomial_mul_naive([],[],mod),lambda:polynomial_divmod_naive([],[],mod),lambda:polynomial_is_zero([],mod)):
                with self.assertRaises(ValueError):fn()


if __name__ == '__main__':
    unittest.main()
