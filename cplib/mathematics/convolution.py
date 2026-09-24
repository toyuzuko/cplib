#!/usr/bin/env python3

from __future__ import annotations

from array import array

from cplib.mathematics.factorization import PrimeFactor
from cplib.mathematics.modular import chinese_remainder_theorem


class ConvolutionMod:
    """
    Convolution over a prime modulus using an NTT-style FFT.

    The class stores the modulus and the precomputed roots needed for
    butterfly transforms. ``convolution`` returns the ordinary polynomial
    product of two coefficient arrays, and ``autoconvolution`` returns the
    self-convolution. ``convolution2d`` handles rectangular coefficient arrays,
    and ``middle_product`` returns sliding dot products of two arrays. All
    operations use the modulus selected by ``set_mod``.

    Attributes:
        _mod: Current modulus.
        _rank2: Exponent of the largest power of two dividing ``mod - 1``.
        _root: Primitive root modulo ``_mod``.
        _imag: Principal fourth root used by the radix-4 butterfly, or ``1``
            when only transforms of length one or two are supported.
        _iimag: Inverse of ``_imag``.
        _rate2: Precomputed radix-2 butterfly factors.
        _irate2: Precomputed inverse radix-2 butterfly factors.
        _rate3: Precomputed radix-4 butterfly factors.
        _irate3: Precomputed inverse radix-4 butterfly factors.

    Space Complexity:
        ``O(n + m)`` for the padded working arrays.

    Notes:
        The default modulus ``998244353`` is tuned for fast NTT execution on
        PyPy. ``set_mod`` supports other prime moduli, but they may be slower.
    """
    _mod = 998244353
    _rank2 = 23 # 998244353 - 1 = 2^23 * 7 * 17
    _root = 3
    _imag = 911660635
    _iimag = 86583718
    _rate2 = (911660635, 509520358, 369330050, 332049552, 983190778, 123842337, 238493703, 975955924, 603855026, 856644456, 131300601, 842657263, 730768835, 942482514, 806263778, 151565301, 510815449, 503497456, 743006876, 741047443, 56250497, 867605899)
    _irate2 = (86583718, 372528824, 373294451, 645684063, 112220581, 692852209, 155456985, 797128860, 90816748, 860285882, 927414960, 354738543, 109331171, 293255632, 535113200, 308540755, 121186627, 608385704, 438932459, 359477183, 824071951, 103369235)
    _rate3 = (372528824, 337190230, 454590761, 816400692, 578227951, 180142363, 83780245, 6597683, 70046822, 623238099, 183021267, 402682409, 631680428, 344509872, 689220186, 365017329, 774342554, 729444058, 102986190, 128751033, 395565204)
    _irate3 = (509520358, 929031873, 170256584, 839780419, 282974284, 395914482, 444904435, 72135471, 638914820, 66769500, 771127074, 985925487, 262319669, 262341272, 625870173, 768022760, 859816005, 914661783, 430819711, 272774365, 530924681)

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set the modulus used by all subsequent transforms.

        Args:
            mod: Prime modulus. The supported transform length is the largest
                power of two dividing mod - 1.

        Returns:
            None.

        Raises:
            ValueError: If mod is not prime. Above 64 bits, the primality test
                is probabilistic.

        Time Complexity:
            Primality testing and primitive-root search, plus O(log mod)
            modular operations to build transform tables. O(1) if unchanged.
        """
        if mod == cls._mod:
            return
        if not PrimeFactor.is_prime(mod):
            raise ValueError('mod must be prime')
        primitive_root = PrimeFactor.primitive_root(mod)
        cls._mod = mod
        cls._root = primitive_root
        cls._rank2 = ((mod - 1) & -(mod - 1)).bit_length() - 1
        root = [0] * (cls._rank2 + 1)
        iroot = [0] * (cls._rank2 + 1)
        root[cls._rank2] = pow(cls._root, (mod - 1) >> cls._rank2, mod)
        iroot[cls._rank2] = pow(root[cls._rank2], mod - 2, mod)
        for i in range(cls._rank2 - 1, -1, -1):
            root[i] = root[i + 1] * root[i + 1] % mod
            iroot[i] = iroot[i + 1] * iroot[i + 1] % mod
        cls._imag = root[2] if cls._rank2 >= 2 else 1
        cls._iimag = iroot[2] if cls._rank2 >= 2 else 1
        cls._rate2, cls._irate2 = cls._calculate_rates(root, iroot, 2)
        cls._rate3, cls._irate3 = cls._calculate_rates(root, iroot, 3)

    @classmethod
    def get_mod(cls) -> int:
        """
        Return the current modulus.

        Returns:
            The prime modulus currently used for transforms.

        Time Complexity:
            O(1)
        """
        return cls._mod

    @classmethod
    def _calculate_rates(cls, root: list[int], iroot: list[int], ofs: int) -> tuple[list[int], list[int]]:
        """Precompute the multiplicative steps used by the butterfly."""
        rate = [0] * max(0, cls._rank2 - (ofs - 1))
        irate = [0] * max(0, cls._rank2 - (ofs - 1))
        prod, iprod = 1, 1
        for i in range(cls._rank2 - (ofs - 1)):
            rate[i] = root[i + ofs] * prod % cls._mod
            irate[i] = iroot[i + ofs] * iprod % cls._mod
            prod *= iroot[i + ofs]
            prod %= cls._mod
            iprod *= root[i + ofs]
            iprod %= cls._mod
        return rate, irate

    @classmethod
    def butterfly(cls, a: list[int]) -> None:
        """
        Apply the forward butterfly transform in-place.

        Args:
            a: Coefficient array. Its length must be a supported power of two,
                or zero (a no-op). Entries may be any integers.

        Returns:
            None. Replaces a with its transform, reduced modulo get_mod().

        Raises:
            ValueError: If the nonzero length is not a supported power of two.

        Notes:
            The forward transform produces bit-reversed frequency order.
            The inverse consumes that order and is unnormalized: applying
            forward and inverse transforms multiplies each entry by len(a).

        Time Complexity:
            O(n log(n + 1)).

        Space Complexity:
            O(1) auxiliary space.
        """
        n = len(a)
        if n == 0:
            return
        if n & (n - 1) or n > 1 << cls._rank2:
            raise ValueError('transform length must be a supported power of two')
        if n == 1:
            a[0] %= cls._mod
            return
        h = (n - 1).bit_length()
        for len_ in range(0, h - 1, 2):
            p = 1 << (h - len_ - 2)
            rot = 1
            for s in range(1 << len_):
                rot2 = rot * rot % cls._mod
                rot3 = rot2 * rot % cls._mod
                offset = s << (h - len_)
                for i in range(p):
                    a0 = a[i + offset]
                    a1 = a[i + offset + p] * rot % cls._mod
                    a2 = a[i + offset + p * 2] * rot2 % cls._mod
                    a3 = a[i + offset + p * 3] * rot3 % cls._mod
                    a1na3imag = (a1 - a3) * cls._imag % cls._mod
                    a[i + offset] = (a0 + a2 + a1 + a3) % cls._mod
                    a[i + offset + p] = (a0 + a2 - a1 - a3) % cls._mod
                    a[i + offset + p * 2] = (a0 - a2 + a1na3imag) % cls._mod
                    a[i + offset + p * 3] = (a0 - a2 - a1na3imag) % cls._mod
                if s + 1 != 1 << len_:
                    rot *= cls._rate3[(~s & -~s).bit_length() - 1]
                    rot %= cls._mod
        if h & 1:
            rot = 1
            for s in range(1 << (h - 1)):
                offset = s << 1
                l = a[offset]
                r = a[offset + 1] * rot % cls._mod
                a[offset] = (l + r) % cls._mod
                a[offset + 1] = (l - r) % cls._mod
                if s + 1 != 1 << (h - 1):
                    rot *= cls._rate2[(~s & -~s).bit_length() - 1]
                    rot %= cls._mod

    @classmethod
    def butterfly_inv(cls, a: list[int]) -> None:
        """
        Apply the inverse butterfly transform in-place.

        Args:
            a: Coefficient array. Its length must be a supported power of two,
                or zero (a no-op). Entries may be any integers.

        Returns:
            None. Replaces a with its transform, reduced modulo get_mod().

        Raises:
            ValueError: If the nonzero length is not a supported power of two.

        Notes:
            The forward transform produces bit-reversed frequency order.
            The inverse consumes that order and is unnormalized: applying
            forward and inverse transforms multiplies each entry by len(a).

        Time Complexity:
            O(n log(n + 1)).

        Space Complexity:
            O(1) auxiliary space.
        """
        n = len(a)
        if n == 0:
            return
        if n & (n - 1) or n > 1 << cls._rank2:
            raise ValueError('transform length must be a supported power of two')
        if n == 1:
            a[0] %= cls._mod
            return
        h = (n - 1).bit_length()

        for len_ in range(h, 1, -2):
            p = 1 << (h - len_)
            irot = 1
            for s in range(1 << (len_ - 2)):
                irot2 = irot * irot % cls._mod
                irot3 = irot2 * irot % cls._mod
                offset = s << (h - len_ + 2)
                for i in range(p):
                    a0 = a[i + offset]
                    a1 = a[i + offset + p]
                    a2 = a[i + offset + p * 2]
                    a3 = a[i + offset + p * 3]
                    a2na3iimag = (a2 - a3) * cls._iimag % cls._mod
                    a[i + offset] = (a0 + a1 + a2 + a3) % cls._mod
                    a[i + offset + p] = (a0 - a1 + a2na3iimag) * irot % cls._mod
                    a[i + offset + p * 2] = (a0 + a1 - a2 - a3) * irot2 % cls._mod
                    a[i + offset + p * 3] = (a0 - a1 - a2na3iimag) * irot3 % cls._mod
                if s + 1 != (1 << (len_ - 2)):
                    irot *= cls._irate3[(~s & -~s).bit_length() - 1]
                    irot %= cls._mod
        if h & 1:
            p = 1 << (h - 1)
            for i in range(p):
                l = a[i]
                r = a[i + p]
                a[i] = (l + r) % cls._mod
                a[i + p] = (l - r) % cls._mod


    @classmethod
    def convolution(cls, a: list[int], b: list[int]) -> list[int]:
        """
        Return the convolution of ``a`` and ``b``.

        Args:
            a: Left coefficient array.
            b: Right coefficient array.

        Returns:
            The product coefficients reduced modulo get_mod(), or [] if
            either input is empty. Neither input is modified.

        Raises:
            ValueError: If the result length exceeds the supported transform
                size.

        Time Complexity:
            ``O((n + m) log (n + m))``
        """
        n, m = len(a), len(b)
        if not n or not m:
            return []
        if n + m - 1 > (1 << cls._rank2):
            raise ValueError('rank2 of given mod is too small.')
        z = 1 << (n + m - 2).bit_length()
        a = a + [0] * (z - n)
        b = b + [0] * (z - m)
        cls.butterfly(a)
        cls.butterfly(b)
        for i in range(z):
            a[i] *= b[i]
            a[i] %= cls._mod
        cls.butterfly_inv(a)
        a = a[:n + m - 1]
        iz = pow(z, -1, cls._mod)
        for i in range(n + m - 1):
            a[i] *= iz
            a[i] %= cls._mod
        return a

    @classmethod
    def convolution2d(cls, left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
        """Return the two-dimensional convolution under the current modulus.

        Args:
            left: Rectangular coefficient array indexed by row and column.
            right: Rectangular coefficient array indexed by row and column.

        Returns:
            A rectangular array with ``h_left + h_right - 1`` rows and
            ``w_left + w_right - 1`` columns, reduced modulo ``get_mod()``.
            Returns ``[]`` if either input has no rows or no columns.
            Neither input is modified.

        Raises:
            ValueError: If either array has unequal row lengths, or the
                flattened result exceeds the supported transform size.
                Both shapes are checked even when one input is empty.

        Time Complexity:
            O(H W log(H W)), where H and W are the output dimensions.

        Space Complexity:
            O(H W).

        Examples:
            >>> ConvolutionMod.convolution2d([[1, 2], [3, 4]], [[1, 1]])
            [[1, 3, 2], [3, 7, 4]]
        """
        height_left = len(left)
        height_right = len(right)
        width_left = len(left[0]) if height_left else 0
        width_right = len(right[0]) if height_right else 0
        if any(len(row) != width_left for row in left) or any(len(row) != width_right for row in right):
            raise ValueError('coefficient arrays must be rectangular')
        if not height_left or not height_right or not width_left or not width_right:
            return []
        height = height_left + height_right - 1
        width = width_left + width_right - 1
        if height * width > 1 << cls._rank2:
            raise ValueError('rank2 of given mod is too small.')
        flat_left = [0] * ((height_left - 1) * width + width_left)
        flat_right = [0] * ((height_right - 1) * width + width_right)
        for x, row in enumerate(left):
            flat_left[x * width:x * width + width_left] = row
        for x, row in enumerate(right):
            flat_right[x * width:x * width + width_right] = row
        flat = cls.convolution(flat_left, flat_right)
        return [flat[x * width:(x + 1) * width] for x in range(height)]

    @classmethod
    def middle_product(cls, left: list[int], right: list[int]) -> list[int]:
        """Return sliding dot products under the current modulus.

        Args:
            left: Coefficient array of length n.
            right: Coefficient array of length m, with m <= n.

        Returns:
            The n - m + 1 values ``sum(left[i+j] * right[j] for j in
            range(m))``, reduced modulo ``get_mod()``. If right is empty,
            returns n + 1 zeros. Neither input is modified.

        Raises:
            ValueError: If left is shorter than right, or the underlying
                convolution exceeds the supported transform size.

        Time Complexity:
            O((n + m) log(n + m)) for nonempty right; O(n + 1) otherwise.

        Space Complexity:
            O(n + m + 1).

        Examples:
            >>> ConvolutionMod.middle_product([1, 2, 3, 4], [2, 1])
            [4, 7, 10]
            >>> ConvolutionMod.middle_product([1, 2], [])
            [0, 0, 0]
        """
        if len(left) < len(right):
            raise ValueError('middle_product requires len(left) >= len(right)')
        if not right:
            return [0] * (len(left) + 1)
        flat = cls.convolution(left, right[::-1])
        return flat[len(right) - 1:len(left)]

    @classmethod
    def autoconvolution(cls, a: list[int]) -> list[int]:
        """
        Return the self-convolution of ``a``.

        Args:
            a: Coefficients to convolve with themselves; the input is not modified.

        Returns:
            Coefficients of a * a, with length 2 * len(a) - 1, or [] for empty a.

        Examples:
            >>> ConvolutionMod.autoconvolution([1, 2])
            [1, 4, 4]
            >>> ConvolutionMod.autoconvolution([])
            []

        Raises:
            ValueError: If the transform length exceeds the modulus capacity.

        Time Complexity:
            O(n log(n + 1)), where n = len(a).

        Space Complexity:
            O(n) auxiliary space.
        """
        n = len(a)
        if n + n - 1 > (1 << cls._rank2):
            raise ValueError('rank2 of given mod is too small.')
        if n == 0: return []
        length = n + n - 1
        z = 1 << (length - 1).bit_length()
        a = a + [0] * (z - n)
        cls.butterfly(a)
        for i in range(z):
            a[i] *= a[i]
            a[i] %= cls._mod
        cls.butterfly_inv(a)
        iz = pow(z, -1, cls._mod)
        for i in range(length):
            a[i] *= iz
            a[i] %= cls._mod
        return a[:length]


class _ConvolutionMod0(ConvolutionMod):
    _mod = 998244353
    _rank2 = 23
    _root = 3
    _imag = 911660635
    _iimag = 86583718
    _rate2 = (911660635, 509520358, 369330050, 332049552, 983190778, 123842337, 238493703, 975955924, 603855026, 856644456, 131300601, 842657263, 730768835, 942482514, 806263778, 151565301, 510815449, 503497456, 743006876, 741047443, 56250497, 867605899)
    _irate2 = (86583718, 372528824, 373294451, 645684063, 112220581, 692852209, 155456985, 797128860, 90816748, 860285882, 927414960, 354738543, 109331171, 293255632, 535113200, 308540755, 121186627, 608385704, 438932459, 359477183, 824071951, 103369235)
    _rate3 = (372528824, 337190230, 454590761, 816400692, 578227951, 180142363, 83780245, 6597683, 70046822, 623238099, 183021267, 402682409, 631680428, 344509872, 689220186, 365017329, 774342554, 729444058, 102986190, 128751033, 395565204)
    _irate3 = (509520358, 929031873, 170256584, 839780419, 282974284, 395914482, 444904435, 72135471, 638914820, 66769500, 771127074, 985925487, 262319669, 262341272, 625870173, 768022760, 859816005, 914661783, 430819711, 272774365, 530924681)


class _ConvolutionMod1(ConvolutionMod):
    _mod = 943718401
    _rank2 = 22
    _root = 7
    _imag = 30720
    _iimag = 943687681
    _rate2 = (30720, 531145428, 579552750, 341274881, 413422744, 267973095, 868515140, 683174150, 563998511, 57476836, 364347547, 617349545, 552773608, 669433986, 664244695, 331636124, 134138688, 258224669, 372790325, 183461426, 281105696)
    _irate2 = (943687681, 840113271, 779281113, 200828821, 768609966, 610479896, 122004786, 254823485, 153081227, 868471187, 927847274, 360815246, 890644352, 336083225, 526085830, 892831155, 189796213, 210621636, 677915858, 836272781, 488822660)
    _rate3 = (840113271, 612845135, 196627611, 728173423, 77866477, 922186129, 700086562, 308133961, 934992050, 256407980, 13035904, 880048567, 444373729, 517763978, 421590485, 465956594, 708671275, 95987865, 48715948, 543611970)
    _irate3 = (531145428, 732605208, 569524618, 136237500, 573377953, 462462852, 910395496, 837217144, 428050031, 602326524, 671981026, 633106753, 746353341, 764637926, 458525064, 696336419, 780417737, 402515508, 546198103, 758799913)


class _ConvolutionMod2(ConvolutionMod):
    _mod = 918552577
    _rank2 = 22
    _root = 5
    _imag = 109585714
    _iimag = 808966863
    _rate2 = (109585714, 495845309, 277035987, 288518669, 507595846, 269036312, 746017139, 213526687, 431178988, 483769052, 612425765, 54024469, 750333289, 84012807, 134157507, 43834559, 581071819, 839889356, 69313940, 766106220, 174694484)
    _irate2 = (808966863, 328441654, 665310863, 28647852, 771705471, 294621512, 689248837, 141866308, 460257477, 762107064, 493717808, 55387233, 617637154, 874411986, 756877493, 464918429, 288190349, 635205505, 457124114, 662233583, 635127911)
    _rate3 = (328441654, 501668940, 372305510, 14351082, 450568404, 27097147, 644756765, 822650257, 418357789, 266224134, 744953423, 883761368, 562807356, 808846395, 15920197, 825043506, 850019262, 467832019, 640394198, 716140614)
    _irate3 = (495845309, 758681881, 613791500, 73657050, 491687210, 185834819, 82052628, 603769954, 23803293, 46795228, 822719472, 398635061, 396560775, 424409110, 871107154, 23426457, 384260597, 19564573, 314170945, 536947424)


class _ConvolutionMod3(ConvolutionMod):
    _mod = 985661441
    _rank2 = 22
    _root = 3
    _imag = 787252466
    _iimag = 198408975
    _rate2 = (787252466, 911296116, 239809280, 927176693, 414885346, 572452974, 646518941, 341831141, 807184077, 545666936, 934943586, 125391471, 19120990, 943004163, 75113924, 191745559, 224896516, 544972411, 452343381, 747827792, 260357423)
    _irate2 = (198408975, 347485208, 354499514, 971597575, 911596184, 204219699, 341924872, 382643016, 649959398, 948752296, 759541610, 646013041, 819248392, 90092732, 661600015, 104651474, 127320746, 657437541, 792717939, 858342966, 289526282)
    _rate3 = (347485208, 871864152, 486029718, 831587864, 358571220, 352250843, 942602674, 199623573, 807411488, 744620642, 369949444, 361373315, 809205263, 214783057, 48485127, 567287823, 403014358, 974543864, 947934590, 116786890)
    _irate3 = (911296116, 460456839, 445259240, 900127251, 189491988, 640287145, 975721816, 320670505, 98289101, 64897625, 365802333, 206410903, 805450301, 333795439, 549996505, 527697008, 56145015, 791290883, 597468121, 894096203)


class _ConvolutionMod4(ConvolutionMod):
    _mod = 924844033
    _rank2 = 21
    _root = 5
    _imag = 502955833
    _iimag = 421888200
    _rate2 = (502955833, 488711599, 801442818, 157266355, 711173591, 295422887, 648823206, 475842151, 571426099, 612742011, 256538483, 560361625, 890270718, 30533833, 251691139, 887364890, 236917564, 818770855, 346731822, 804593178)
    _irate2 = (421888200, 488754607, 395044753, 407100045, 92817111, 457487221, 719862406, 404246757, 854742170, 367570384, 241303542, 509956364, 330538969, 561535662, 328101217, 505704979, 879334380, 309864919, 473569592, 12282549)
    _rate3 = (488754607, 101592004, 160127150, 104736910, 595245657, 595586882, 748595602, 438496620, 181426929, 372496886, 621478322, 474299229, 140848104, 285411294, 612033415, 482349559, 160059414, 370339186, 225572535)
    _irate3 = (488711599, 835495420, 735613250, 24102664, 134171761, 305923422, 866968153, 157518758, 635520105, 9000928, 95138417, 113352337, 415183532, 244263092, 153196429, 350541386, 783438994, 737631038, 215572186)


class ConvolutionLargeIntegers:
    """
    Convolution for large integers via multi-modulus CRT reconstruction.

    The method computes the convolution under several NTT-friendly moduli and
    reconstructs the exact integer result by the Chinese Remainder Theorem.

    Space Complexity:
        ``O(k * n)`` for the temporary transformed arrays.

    Examples:
        >>> ConvolutionLargeIntegers.convolution([1, 2], [3, 4])
        [3, 10, 8]
    """
    _mods = (998244353, 943718401, 918552577, 985661441, 924844033)
    _convolution_classes = (_ConvolutionMod0, _ConvolutionMod1, _ConvolutionMod2, _ConvolutionMod3, _ConvolutionMod4)

    @classmethod
    def _determine_num_mods(cls, a: list[int], b: list[int]) -> int:
        """Return the number of moduli for safe reconstruction, or 0 for fallback."""
        n, m = len(a), len(b)
        max_val_a = max(abs(x) for x in a) if a else 0
        max_val_b = max(abs(x) for x in b) if b else 0
        max_result = max_val_a * max_val_b * min(n, m)

        prod = 1
        for i in range(len(cls._mods)):
            prod *= cls._mods[i]
            if prod > 2 * max_result:
                return i + 1

        return 0

    @classmethod
    def convolution(cls, a: list[int], b: list[int], mod: int = 0) -> list[int]:
        """
        Return the exact or modular convolution of two integer arrays.

        Args:
            a: Left coefficient array.
            b: Right coefficient array.
            mod: Optional modulus for the final result. ``0`` means exact
                reconstruction.

        Returns:
            The convolution of ``a`` and ``b``, or [] if either input is empty.

        Raises:
            ValueError: If mod is negative, or the result exceeds the NTT
                capacity of a modulus needed for CRT reconstruction.

        Time Complexity:
            ``O(k * (n + m) log (n + m))`` where ``k`` is the number of
            moduli used for the reconstruction. If the coefficient bound
            exceeds the available CRT range, exact O(nm) multiplication is used.
        """
        if mod < 0:
            raise ValueError('mod must be nonnegative')
        n, m = len(a), len(b)
        if not n or not m:
            return []

        num_mods = cls._determine_num_mods(a, b)
        if num_mods == 0:
            # The available CRT moduli cannot uniquely recover these coefficients.
            result = [0] * (n + m - 1)
            for i, x in enumerate(a):
                for j, y in enumerate(b):
                    result[i + j] += x * y
            return [x % mod for x in result] if mod else result

        results: list[list[int]] = []
        for i in range(num_mods):
            conv_class = cls._convolution_classes[i]
            a_mod = [x % conv_class.get_mod() for x in a]
            b_mod = [x % conv_class.get_mod() for x in b]
            result = conv_class.convolution(a_mod, b_mod)
            results.append(result)

        final_result: list[int] = []
        for i in range(n + m - 1):
            remainders: list[int] = []
            moduli: list[int] = []
            for j in range(num_mods):
                remainders.append(results[j][i])
                moduli.append(cls._mods[j])

            value, modulus_product = chinese_remainder_theorem(remainders, moduli)
            if value > modulus_product // 2:
                value -= modulus_product
            if mod > 0:
                value %= mod
            final_result.append(value)

        return final_result

    @classmethod
    def autoconvolution(cls, a: list[int], mod: int = 0) -> list[int]:
        """
        Return the exact or modular self-convolution of ``a``.

        Args:
            a: Signed integer coefficients to convolve with themselves.
            mod: Positive output modulus, or 0 for exact integer coefficients.

        Returns:
            Coefficients of a * a, with length 2 * len(a) - 1, or [] for empty a.

        Raises:
            ValueError: If mod is negative, or the result exceeds the NTT
                capacity of a modulus needed for CRT reconstruction.

        Time Complexity:
            ``O(k * n log n)`` where ``k`` is the number of moduli used for
            the reconstruction. If the coefficient bound exceeds the available
            CRT range, exact O(n**2) multiplication is used.
        """
        if mod < 0:
            raise ValueError('mod must be nonnegative')
        n = len(a)
        if n == 0:
            return []

        num_mods = cls._determine_num_mods(a, a)
        if num_mods == 0:
            return cls.convolution(a, a, mod)

        results: list[list[int]] = []
        for i in range(num_mods):
            conv_class = cls._convolution_classes[i]
            a_mod = [x % conv_class.get_mod() for x in a]
            result = conv_class.autoconvolution(a_mod)
            results.append(result)

        final_result: list[int] = []
        for i in range(n + n - 1):
            remainders: list[int] = []
            moduli: list[int] = []
            for j in range(num_mods):
                remainders.append(results[j][i])
                moduli.append(cls._mods[j])

            value, modulus_product = chinese_remainder_theorem(remainders, moduli)
            if value > modulus_product // 2:
                value -= modulus_product
            if mod > 0:
                value %= mod
            final_result.append(value)

        return final_result


class Convolution64bit:
    """
    Convolution modulo ``2**64`` using Garner-style reconstruction.

    The class reuses the same NTT transforms as
    :class:`ConvolutionLargeIntegers` and reconstructs the answer with
    fixed-width arithmetic.

    Space Complexity:
        ``O(n)``.

    This is intended for exact 64-bit wraparound semantics rather than modular
    arithmetic over an arbitrary prime.
    """
    _mods = (998244353, 943718401, 918552577, 985661441, 924844033)
    _convolution_classes = (_ConvolutionMod0, _ConvolutionMod1, _ConvolutionMod2, _ConvolutionMod3, _ConvolutionMod4)

    # Precomputed constants for CRT reconstruction mod 2^64
    # inv[i] = inverse of previous product mod mods[i+1]
    _invs = (145187429, 846035689, 564674830, 846925072)

    # Precomputed products for efficient reconstruction
    # _prod01 = _mods[0] * _mods[1]
    # _prod012 = _mods[0] * _mods[1] * _mods[2]
    # etc.
    _prod01 = 942061564620439553
    _prod012 = 865333077874756778280878081
    _prod0123 = 852925448482997983604847792063774721

    @classmethod
    def convolution(cls, a: list[int], b: list[int]) -> list[int]:
        """
        Return the convolution of ``a`` and ``b`` modulo ``2**64``.

        Args:
            a: Left integer coefficients; each is reduced modulo 2**64.
            b: Right integer coefficients; each is reduced modulo 2**64.

        Returns:
            The product coefficients in [0, 2**64), or [] if either input is
            empty. Neither input is modified.

        Raises:
            ValueError: If the nonempty result length exceeds 2**21, the
                capacity of the smallest transform used for reconstruction.

        Time Complexity:
            ``O((n + m) log (n + m))``
        """
        n, m = len(a), len(b)
        if not n or not m:
            return []

        if n + m - 1 > 1 << 21:
            raise ValueError('result length exceeds the transform capacity')
        mask = (1 << 64) - 1
        a = [x & mask for x in a]
        b = [x & mask for x in b]

        # Perform convolution with each modulus
        results: list[list[int]] = []
        for i in range(5):
            conv_class = cls._convolution_classes[i]
            a_mod = [x % conv_class.get_mod() for x in a]
            b_mod = [x % conv_class.get_mod() for x in b]
            result = conv_class.convolution(a_mod, b_mod)
            results.append(result)

        # Reconstruct using optimized CRT for mod 2^64
        final_result: list[int] = []
        for i in range(n + m - 1):
            # Garner's algorithm optimized for mod 2^64
            v0 = results[0][i]
            v1 = (results[1][i] - v0) * cls._invs[0] % cls._mods[1]
            v2 = ((results[2][i] - v0 - v1 * cls._mods[0]) % cls._mods[2]) * cls._invs[1] % cls._mods[2]
            v3 = ((results[3][i] - v0 - v1 * cls._mods[0] - v2 * cls._prod01) % cls._mods[3]) * cls._invs[2] % cls._mods[3]
            v4 = ((results[4][i] - v0 - v1 * cls._mods[0] - v2 * cls._prod01 - v3 * cls._prod012) % cls._mods[4]) * cls._invs[3] % cls._mods[4]

            # Reconstruct the value mod 2^64 using bit operations
            # Since we're working mod 2^64, all operations are automatically mod 2^64 in Python with & ((1<<64)-1)
            value = v0
            value += v1 * cls._mods[0]
            value += v2 * cls._prod01
            value += v3 * cls._prod012
            value += v4 * cls._prod0123

            # Ensure result is in [0, 2^64)
            value &= (1 << 64) - 1
            final_result.append(value)

        return final_result

    @classmethod
    def autoconvolution(cls, a: list[int]) -> list[int]:
        """
        Return the self-convolution of ``a`` modulo ``2**64``.

        Args:
            a: Integer coefficients, reduced modulo 2**64 before convolution.

        Returns:
            Coefficients of a * a, with length 2 * len(a) - 1, or [] for empty a.

        Raises:
            ValueError: If the nonempty result length exceeds 2**21.

        Time Complexity:
            ``O(n log n)``
        Space Complexity:
            ``O(n)``
        """
        n = len(a)
        if n == 0:
            return []

        if 2 * n - 1 > 1 << 21:
            raise ValueError('result length exceeds the transform capacity')
        a = [x & ((1 << 64) - 1) for x in a]

        # Perform auto-convolution with each modulus
        results: list[list[int]] = []
        for i in range(5):
            conv_class = cls._convolution_classes[i]
            a_mod = [x % conv_class.get_mod() for x in a]
            result = conv_class.autoconvolution(a_mod)
            results.append(result)

        # Reconstruct using optimized CRT for mod 2^64
        final_result: list[int] = []
        for i in range(n + n - 1):
            v0 = results[0][i]
            v1 = (results[1][i] - v0) * cls._invs[0] % cls._mods[1]
            v2 = ((results[2][i] - v0 - v1 * cls._mods[0]) % cls._mods[2]) * cls._invs[1] % cls._mods[2]
            v3 = ((results[3][i] - v0 - v1 * cls._mods[0] - v2 * cls._prod01) % cls._mods[3]) * cls._invs[2] % cls._mods[3]
            v4 = ((results[4][i] - v0 - v1 * cls._mods[0] - v2 * cls._prod01 - v3 * cls._prod012) % cls._mods[4]) * cls._invs[3] % cls._mods[4]

            # Reconstruct the value mod 2^64 using bit operations
            value = v0
            value += v1 * cls._mods[0]
            value += v2 * cls._prod01
            value += v3 * cls._prod012
            value += v4 * cls._prod0123

            # Ensure result is in [0, 2^64)
            value &= (1 << 64) - 1
            final_result.append(value)

        return final_result


_BF64_SUBTABLES: list[array[int]] = []


def _bf64_mul(a: int, b: int) -> int:
    """
    Multiply two ``F_{2^64}`` elements held in signed two's-complement form.

    Operands and result use the signed reinterpretation that keeps 64-bit
    values unboxed in PyPy. ``_bf64_prepare`` must have run first.
    This module-level kernel is the convolution hot path.

    Time Complexity:
        ``O(64)`` table lookups.

    Space Complexity:
        ``O(1)``.
    """
    sub = _BF64_SUBTABLES
    av = (
        (a & 255) << 8, ((a >> 8) & 255) << 8, ((a >> 16) & 255) << 8, ((a >> 24) & 255) << 8,
        ((a >> 32) & 255) << 8, ((a >> 40) & 255) << 8, ((a >> 48) & 255) << 8, ((a >> 56) & 255) << 8,
    )
    bv = (
        b & 255, (b >> 8) & 255, (b >> 16) & 255, (b >> 24) & 255,
        (b >> 32) & 255, (b >> 40) & 255, (b >> 48) & 255, (b >> 56) & 255,
    )
    res = 0
    idx = 0
    for e in range(8):
        ae = av[e]
        for f in range(8):
            res ^= sub[idx][ae | bv[f]]
            idx += 1
    return res


_BF64_MOD = (1 << 64) | 0b11011


def _bf64_clmul(a: int, b: int) -> int:
    """Carry-less (polynomial) multiplication over ``F_2``."""
    res = 0
    while b:
        lsb = b & -b
        res ^= a << (lsb.bit_length() - 1)
        b ^= lsb
    return res


def _bf64_reduce(x: int) -> int:
    """Reduce ``x`` modulo ``x^64 + x^4 + x^3 + x + 1``."""
    while x.bit_length() > 64:
        x ^= _BF64_MOD << (x.bit_length() - 65)
    return x


def _bf64_prepare() -> None:
    """
    Build the byte-pair multiplication tables once.

    Tables are stored as signed 64-bit (``array('q')``) holding the
    two's-complement reinterpretation of each field element. PyPy keeps signed
    machine-word ints unboxed, while values >= 2^63 stored as unsigned would
    fall back to slow bignums. XOR is closed under this reinterpretation, so the
    field arithmetic stays bit-for-bit correct.
    """
    if _BF64_SUBTABLES:
        return
    sign = 1 << 63
    full = 1 << 64
    subtables: list[array[int]] = []
    for e in range(8):
        for f in range(8):
            table = array('q', [0]) * 65536
            shift = (e + f) * 8
            for x in range(1, 256):
                lsb = x & -x
                prev = (x ^ lsb) << 8
                cur = x << 8
                p = lsb.bit_length() - 1
                for y in range(256):
                    r = _bf64_reduce(_bf64_clmul(1 << p, y) << shift)
                    table[cur | y] = table[prev | y] ^ (r - full if r >= sign else r)
            subtables.append(table)
    _BF64_SUBTABLES.extend(subtables)


class BinaryField64:
    """
    Arithmetic in ``F_2[x] / (x^64 + x^4 + x^3 + x + 1)``.

    Field elements are 64-bit. The convolution routines operate on the signed
    two's-complement reinterpretation so values stay unboxed in PyPy, while the
    public methods reduce integer operands to their low 64 bits and return
    unsigned values in ``[0, 2^64)``.

    Space Complexity:
        O(1) per value, plus fixed-size module tables after initialization.
    """

    _mask = (1 << 64) - 1

    @classmethod
    def add(cls, a: int, b: int) -> int:
        """
        Add two field elements.

        Args:
            a: First field element.
            b: Second field element.

        Returns:
            ``a + b`` in the field.

        Time Complexity:
            ``O(1)``.
        """
        return (a ^ b) & cls._mask

    @classmethod
    def multiply(cls, a: int, b: int) -> int:
        """
        Multiply two field elements.

        Args:
            a: First field element.
            b: Second field element.

        Returns:
            ``a * b`` in ``F_2[x] / (x^64 + x^4 + x^3 + x + 1)`` as an unsigned
            value in ``[0, 2^64)``.

        Time Complexity:
            ``O(64)`` after table initialization.
        """
        _bf64_prepare()
        return _bf64_mul(a, b) & cls._mask

    @classmethod
    def pow(cls, a: int, n: int) -> int:
        """
        Return ``a ** n`` in the field.

        Args:
            a: Base field element.
            n: Non-negative exponent.

        Returns:
            Power of ``a``. The zeroth power is one, including for zero.

        Raises:
            ValueError: If n is negative.

        Time Complexity:
            ``O(log n)`` field multiplications.
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        res = 1
        while n:
            if n & 1:
                res = cls.multiply(res, a)
            a = cls.multiply(a, a)
            n >>= 1
        return res

    @classmethod
    def inv(cls, a: int) -> int:
        """
        Return the multiplicative inverse of ``a``.

        Args:
            a: Nonzero field element.

        Returns:
            ``a^-1`` in the field.

        Raises:
            ZeroDivisionError: If the low 64 bits of a are zero.

        Time Complexity:
            ``O(log 2^64)`` field multiplications.
        """
        a &= cls._mask
        if a == 0:
            raise ZeroDivisionError('zero has no multiplicative inverse')
        return cls.pow(a, (1 << 64) - 2)


class ConvolutionBinaryField64:
    """
    Convolution over ``F_2[x] / (x^64 + x^4 + x^3 + x + 1)``.

    Space Complexity:
        O(n + m) for convolution operands and transform buffers.
    """

    _pow3 = (1, 3, 9, 27, 81, 243, 729, 2187, 6561, 19683, 59049, 177147, 531441, 1594323)

    @staticmethod
    def _mul_w(z: tuple[int, int]) -> tuple[int, int]:
        return z[1], z[0] ^ z[1]

    @staticmethod
    def _mul_w2(z: tuple[int, int]) -> tuple[int, int]:
        return z[0] ^ z[1], z[0]

    @staticmethod
    def _conj(z: tuple[int, int]) -> tuple[int, int]:
        return z[0] ^ z[1], z[1]

    @staticmethod
    def _add(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
        return a[0] ^ b[0], a[1] ^ b[1]

    @classmethod
    def _mul_pair(cls, a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
        xx = _bf64_mul(a[0], b[0])
        yy = _bf64_mul(a[1], b[1])
        xy_yx = _bf64_mul(a[0] ^ a[1], b[0] ^ b[1]) ^ xx ^ yy
        return xx ^ yy, xy_yx ^ yy

    @classmethod
    def _rotate_right(cls, a: list[tuple[int, int]], l: int, n: int, k: int) -> None:
        if k:
            a[l:l + n] = a[l + n - k:l + n] + a[l:l + n - k]

    @classmethod
    def _rotate_left(cls, a: list[tuple[int, int]], l: int, n: int, k: int) -> None:
        if k:
            a[l:l + n] = a[l + k:l + n] + a[l:l + k]

    @classmethod
    def _mul_range_w(cls, a: list[tuple[int, int]], l: int, n: int, w: int) -> None:
        if w == 0:
            return
        op = cls._mul_w if w == 1 else cls._mul_w2
        for i in range(l, l + n):
            a[i] = op(a[i])

    @classmethod
    def _butterfly_x3(cls, a: list[tuple[int, int]], la: int, lb: int, lc: int, n: int, w: int, inverse: bool) -> None:
        sh1 = w % n
        tw1 = w // n
        sh2 = (2 * w) % n
        tw2 = (2 * w) // n % 3

        if not inverse:
            cls._rotate_right(a, lb, n, sh1)
            cls._rotate_right(a, lc, n, sh2)

            cls._mul_range_w(a, lb, sh1, (1 + tw1) % 3)
            cls._mul_range_w(a, lc, sh2, (1 + tw2) % 3)
            cls._mul_range_w(a, lb + sh1, n - sh1, tw1)
            cls._mul_range_w(a, lc + sh2, n - sh2, tw2)

            for i in range(n):
                x = a[la + i]
                y = a[lb + i]
                z = a[lc + i]
                yw = cls._mul_w(y)
                yw2 = cls._mul_w2(y)
                zw = cls._mul_w(z)
                zw2 = cls._mul_w2(z)
                a[la + i] = (x[0] ^ y[0] ^ z[0], x[1] ^ y[1] ^ z[1])
                a[lb + i] = (x[0] ^ yw[0] ^ zw2[0], x[1] ^ yw[1] ^ zw2[1])
                a[lc + i] = (x[0] ^ yw2[0] ^ zw[0], x[1] ^ yw2[1] ^ zw[1])
        else:
            for i in range(n):
                x = a[la + i]
                y = a[lb + i]
                z = a[lc + i]
                yw = cls._mul_w(y)
                yw2 = cls._mul_w2(y)
                zw = cls._mul_w(z)
                zw2 = cls._mul_w2(z)
                a[la + i] = (x[0] ^ y[0] ^ z[0], x[1] ^ y[1] ^ z[1])
                a[lb + i] = (x[0] ^ yw2[0] ^ zw[0], x[1] ^ yw2[1] ^ zw[1])
                a[lc + i] = (x[0] ^ yw[0] ^ zw2[0], x[1] ^ yw[1] ^ zw2[1])

            cls._mul_range_w(a, lb, sh1, (5 - tw1) % 3)
            cls._mul_range_w(a, lc, sh2, (5 - tw2) % 3)
            cls._mul_range_w(a, lb + sh1, n - sh1, (3 - tw1) % 3)
            cls._mul_range_w(a, lc + sh2, n - sh2, (3 - tw2) % 3)

            cls._rotate_left(a, lb, n, sh1)
            cls._rotate_left(a, lc, n, sh2)

    @classmethod
    def _aux_transform(cls, a: list[tuple[int, int]], lg: int, lg2: int, inverse: bool, conj: bool = False) -> None:
        m = cls._pow3[lg2]
        mod = cls._pow3[lg2 + 1]

        def rec(k: int, offset: int, w: int) -> None:
            n = cls._pow3[k]
            if inverse and k >= lg2 + 1:
                for jj in range(3):
                    rec(k - 1, offset + n * jj, (w // 3 + m * jj) % mod)
            for j in range(0, n, m):
                cls._butterfly_x3(a, offset + j, offset + j + n, offset + j + n * 2, m, w // 3, inverse)
            if not inverse and k >= lg2 + 1:
                for jj in range(3):
                    rec(k - 1, offset + n * jj, (w // 3 + m * jj) % mod)

        rec(lg - 1, 0, (1 + int(conj)) * m)

    @classmethod
    def _convolve_cyclic_naive(cls, a: list[tuple[int, int]], b: list[tuple[int, int]]) -> list[tuple[int, int]]:
        n = len(a)
        res = [(0, 0)] * n
        for i in range(n):
            ai = a[i]
            for j in range(n):
                p = cls._mul_pair(ai, b[j])
                k = i + j
                if k >= n:
                    k -= n
                    p = cls._mul_w(p)
                res[k] = (res[k][0] ^ p[0], res[k][1] ^ p[1])
        return res

    @classmethod
    def _convolve_aux(cls, a: list[tuple[int, int]], b: list[tuple[int, int]], lg: int) -> list[tuple[int, int]]:
        n = cls._pow3[lg]
        if lg <= 3:
            return cls._convolve_cyclic_naive(a, b)

        lg2 = (lg + 1) // 2
        m = cls._pow3[lg2]

        xa = a[:]
        xb = b[:]
        ya = [cls._conj(z) for z in a]
        yb = [cls._conj(z) for z in b]

        cls._aux_transform(xa, lg, lg2, False)
        cls._aux_transform(xb, lg, lg2, False)
        cls._aux_transform(ya, lg, lg2, False, True)
        cls._aux_transform(yb, lg, lg2, False, True)

        for i in range(0, n, m):
            xb[i:i + m] = cls._convolve_aux(xb[i:i + m], xa[i:i + m], lg2)
            yb[i:i + m] = cls._convolve_aux(yb[i:i + m], ya[i:i + m], lg2)

        cls._aux_transform(xb, lg, lg2, True)
        cls._aux_transform(yb, lg, lg2, True, True)
        yb = [cls._conj(z) for z in yb]

        res = [(0, 0)] * n
        for i in range(0, n, m):
            for j in range(m):
                x1 = cls._add(cls._mul_w2(xb[i + j]), cls._mul_w(yb[i + j]))
                x2 = cls._add(xb[i + j], yb[i + j])
                res[i + j] = cls._add(res[i + j], x1)
                k = i + j + m
                if k < n:
                    res[k] = cls._add(res[k], x2)
                else:
                    res[k - n] = cls._add(res[k - n], cls._mul_w(x2))
        return res

    @classmethod
    def convolution(cls, a: list[int], b: list[int]) -> list[int]:
        """
        Return the convolution of ``a`` and ``b`` over ``F_{2^64}``.

        Args:
            a: Left integer coefficients; only their low 64 bits are used.
            b: Right integer coefficients; only their low 64 bits are used.

        Returns:
            Product coefficients in [0, 2**64), or [] if either input is empty.
            Neither input is modified.

        Raises:
            ValueError: If the recursive transform is needed and the result
                length exceeds 2 * 3**13.

        Time Complexity:
            O(len(a)) field multiplications if a == b, since cross terms cancel;
            O(len(a) * len(b)) field multiplications for small inputs otherwise;
            O(N log N log log N) field operations for the recursive transform,
            where N is the smallest power of three with 2N >= len(a)+len(b)-1.
            Each field multiplication uses 64 byte-table lookups.

        Space Complexity:
            O(len(a) + len(b)), in addition to the fixed field tables.
        """
        if not a or not b:
            return []
        if a is b or a == b:
            return cls.autoconvolution(a)
        recursive = len(a) * len(b) > 20000
        if recursive and len(a) + len(b) - 1 > 2 * cls._pow3[-1]:
            raise ValueError('result length exceeds the transform capacity')
        _bf64_prepare()
        # Work in the signed two's-complement reinterpretation throughout so
        # 64-bit values stay unboxed in PyPy; convert back to unsigned on output.
        sign = 1 << 63
        full = 1 << 64
        mask = (1 << 64) - 1
        if recursive:
            lg = 0
            while 2 * cls._pow3[lg] < len(a) + len(b) - 1:
                lg += 1
            n = cls._pow3[lg]
            f = [(0, 0)] * n
            g = [(0, 0)] * n
            for i, x in enumerate(a):
                x &= mask
                xs = x - full if x >= sign else x
                if i < n:
                    f[i] = (xs, 0)
                else:
                    f[i - n] = (f[i - n][0], xs)
            for i, x in enumerate(b):
                x &= mask
                xs = x - full if x >= sign else x
                if i < n:
                    g[i] = (xs, 0)
                else:
                    g[i - n] = (g[i - n][0], xs)
            h = cls._convolve_aux(f, g, lg)
            size = len(a) + len(b) - 1
            return [(h[i][0] if i < n else h[i - n][1]) & mask for i in range(size)]
        res = [0] * (len(a) + len(b) - 1)
        for i, x in enumerate(a):
            for j, y in enumerate(b):
                res[i + j] ^= _bf64_mul(x, y)
        return [r & mask for r in res]

    @classmethod
    def autoconvolution(cls, a: list[int]) -> list[int]:
        """
        Return the self-convolution of ``a`` over ``F_{2^64}``.

        Args:
            a: Integer coefficients; only their low 64 bits are used.

        Returns:
            The product coefficients, or [] for empty a. Odd-indexed
            coefficients are zero in characteristic two.

        Time Complexity:
            O(len(a)) field multiplications after table initialization.

        Space Complexity:
            O(len(a)).
        """
        if not a:
            return []
        _bf64_prepare()
        result = [0] * (2 * len(a) - 1)
        for i, value in enumerate(a):
            result[2 * i] = _bf64_mul(value, value) & ((1 << 64) - 1)
        return result
