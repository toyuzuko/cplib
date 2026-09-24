# cplib.geometry

`cplib.geometry` contains integer, rational, and floating-point geometry algorithms.

## Modules

### `floating.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `set_eps` | function | `set_eps(eps: float) -> None` | Set the module-wide tolerance for floating-point geometry. | Time: O(1) |
| `get_eps` | function | `get_eps() -> float` | Return the current module-wide floating-point tolerance. | Time: O(1) |
| `sgn` | function | `sgn(x: float, eps: float \| None = None) -> int` | Return the sign of ``x`` under a tolerance. | Time: O(1) |
| `equals` | function | `equals(a: float, b: float, eps: float \| None = None) -> bool` | Return whether two floating-point values are equal under tolerance. | Time: O(1) |
| `Point` | class | `Point(x: float, y: float)` | 2D point or vector with floating-point coordinates. | Space: O(1) |
| `Line` | class | `Line(start: Point, end: Point)` | Directed line represented by two points. | Space: O(1) |
| `Segment` | class | `Segment(...)` | Line segment represented by two endpoints. | Space: O(1) |
| `Circle` | class | `Circle(center: Point, radius: float)` | Circle with floating-point center and radius. | Space: O(1) |
| `dot` | function | `dot(p1: Point, p2: Point) -> float` | Return the dot product of two vectors. | Time: O(1) |
| `cross` | function | `cross(p1: Point, p2: Point) -> float` | Return the cross product of two vectors. | Time: O(1) |
| `norm2` | function | `norm2(p: Point) -> float` | Return the squared Euclidean norm of a vector. | Time: O(1) |
| `abs` | function | `abs(p: Point) -> float` | Return the Euclidean norm of a vector. | Time: O(1) |
| `ccw` | function | `ccw(a: Point, b: Point, c: Point) -> int` | Classify the position of ``c`` against directed segment ``a-b``. | Time: O(1) |
| `is_parallel` | function | `is_parallel(line1: LineLike, line2: LineLike) -> bool` | Return whether two lines are parallel. | Time: O(1) |
| `is_orthogonal` | function | `is_orthogonal(line1: LineLike, line2: LineLike) -> bool` | Return whether two lines are orthogonal. | Time: O(1) |
| `projection` | function | `projection(line: LineLike, point: Point) -> Point` | Return the orthogonal projection of a point onto a line. | Time: O(1) |
| `reflection` | function | `reflection(line: LineLike, point: Point) -> Point` | Return the reflection of a point across a line. | Time: O(1) |
| `intersect` | function | `intersect(segment1: Segment, segment2: Segment) -> bool` | Return whether two segments intersect. | Time: O(1) |
| `cross_point` | function | `cross_point(line1: LineLike, line2: LineLike) -> Point` | Return the intersection point of two non-parallel lines. | Time: O(1) |
| `distance_pp` | function | `distance_pp(point1: Point, point2: Point) -> float` | Return the distance between two points. | Time: O(1) |
| `distance_lp` | function | `distance_lp(line: LineLike, point: Point) -> float` | Return the distance from a point to a line. | Time: O(1) |
| `distance_sp` | function | `distance_sp(segment: Segment, point: Point) -> float` | Return the distance from a point to a segment. | Time: O(1) |
| `distance_ss` | function | `distance_ss(segment1: Segment, segment2: Segment) -> float` | Return the distance between two segments. | Time: O(1) |
| `distance` | function | `distance(obj1: Point \| LineLike, obj2: Point \| LineLike) -> float` | Return the Euclidean distance between supported geometry objects. | Time: O(1) |
| `circle_relation` | function | `circle_relation(circle1: Circle, circle2: Circle) -> int` | Classify the positional relationship of two circles. | Time: O(1) |
| `triangle_incircle` | function | `triangle_incircle(a: Point, b: Point, c: Point) -> Circle` | Return the incircle of a triangle. | Time: O(1) |
| `triangle_circumcircle` | function | `triangle_circumcircle(a: Point, b: Point, c: Point) -> Circle` | Return the circumcircle of a triangle. | Time: O(1) |
| `intersect_circle_line` | function | `intersect_circle_line(circle: Circle, line: LineLike) -> bool` | Return whether a circle and an infinite line intersect. | Time: O(1) |
| `intersect_circle_segment` | function | `intersect_circle_segment(circle: Circle, segment: Segment) -> bool` | Return whether a circle and a segment intersect. | Time: O(1) |
| `circle_line_cross_points` | function | `circle_line_cross_points(circle: Circle, line: LineLike) -> tuple[Point, Point]` | Return the intersection points of a circle and an infinite line. | Time: O(1) |
| `circle_circle_cross_points` | function | `circle_circle_cross_points(circle1: Circle, circle2: Circle) -> tuple[Point, Point]` | Return the intersection points of two circles. | Time: O(1) |
| `tangent_points_from_point` | function | `tangent_points_from_point(circle: Circle, point: Point) -> list[Point]` | Return tangent points from an external point to a circle. | Time: O(1) |
| `common_tangent_points` | function | `common_tangent_points(circle1: Circle, circle2: Circle) -> list[Point]` | Return tangent points on the first circle for common tangents. | Time: O(1) |
| `polygon_signed_area` | function | `polygon_signed_area(points: list[Point]) -> float` | Return the signed area of a polygon. | Time: O(n) |
| `polygon_area` | function | `polygon_area(points: list[Point]) -> float` | Return the area of a polygon. | Time: O(n) |
| `is_convex_polygon` | function | `is_convex_polygon(points: list[Point], allow_collinear: bool = True) -> bool` | Return whether a polygon is convex. | Time: O(n) |
| `contains_point_in_polygon` | function | `contains_point_in_polygon(points: list[Point], point: Point) -> int` | Classify a point against a polygon. | Time: O(n) |
| `convex_hull` | function | `convex_hull(points: list[Point], keep_collinear: bool = False) -> list[Point]` | Return the convex hull of a point set. | Time: O(n log n) |
| `convex_polygon_diameter` | function | `convex_polygon_diameter(points: list[Point]) -> tuple[int, int, float]` | Return one farthest pair on a convex polygon. | Time: O(n) |
| `convex_cut` | function | `convex_cut(points: list[Point], line: LineLike) -> list[Point]` | Cut a convex polygon by a directed line. | Time: O(n) |
| `closest_pair_distance` | function | `closest_pair_distance(points: list[Point]) -> float` | Return the minimum Euclidean distance among point pairs. | Time: O(n log n), using bottom-up divide and conquer. |
| `minimum_enclosing_circle` | function | `minimum_enclosing_circle(points: list[Point]) -> Circle` | Return the minimum circle enclosing all points. | Time: Expected O(n) over random shuffling; O(n**3) in the worst case. |
| `circle_circle_intersection_area` | function | `circle_circle_intersection_area(circle1: Circle, circle2: Circle) -> float` | Return the area common to two circles. | Time: O(1) |
| `circle_polygon_intersection_area` | function | `circle_polygon_intersection_area(circle: Circle, polygon: list[Point]) -> float` | Return the area common to a circle and a simple polygon. | Time: O(n), where ``n = len(polygon)``. |
| `koch_curve_points` | function | `koch_curve_points(start: Point, end: Point, depth: int) -> list[Point]` | Return points on a Koch curve segment. | Time: O(4^depth) |

### `integer.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `Point` | class | `Point(x: int, y: int)` | 2D point with integer coordinates. | Space: O(1) |
| `argsort` | function | `argsort(points: list[Point]) -> list[Point]` | Sort points by angle around the origin. | Time: O(n log n), where n is the number of points |
| `closest_points` | function | `closest_points(points: list[Point]) -> tuple[int, int]` | Find the pair of points with minimum Euclidean distance. | Time: O(n log n), where n is the number of points |
| `convex_hull` | function | `convex_hull(points: list[Point]) -> list[int]` | Compute the convex hull of a set of 2D points. | Time: O(n log n), where n is the number of points |
| `convex_layers` | function | `convex_layers(points: list[Point]) -> list[int]` | Compute onion-decomposition layers of distinct integer points. | Time: ``O(n log^2 n)`` |
| `furthest_points` | function | `furthest_points(points: list[Point]) -> tuple[int, int]` | Find the pair of points with maximum Euclidean distance. | Time: O(n log n), where n is the number of points |
| `minimum_enclosing_circle` | function | `minimum_enclosing_circle(points: list[Point]) -> list[bool]` | Return which points lie on the minimum enclosing circle boundary. | Time: Expected O(n), where n is the number of points |
| `Segment` | class | `Segment(start: Point, end: Point)` | Line segment defined by two endpoints. | Space: O(1) |
| `count_manhattan_intersections` | function | `count_manhattan_intersections(segments: list[Segment]) -> int` | Count intersections between horizontal and vertical line segments. | Time: O(n log n), where n is the number of segments. |
| `Circle` | class | `Circle(center: Point, radius: int)` | Circle represented exactly with scaled integer center coordinates. | Space: O(1) |
| `manhattan_mst` | function | `manhattan_mst(points: list[Point]) -> tuple[list[tuple[int, int]], int]` | Compute a minimum spanning tree under Manhattan distance. | Time: O(n log n), where n is the number of points |
| `euclidean_mst` | function | `euclidean_mst(points: list[Point]) -> list[tuple[int, int]]` | Compute a minimum spanning tree under Euclidean distance. | Time: O(n log n), where n is the number of points; the construction is deterministic. This counts integer arithmetic operations. |
| `delaunay_edges` | function | `delaunay_edges(points: list[Point]) -> list[tuple[int, int]]` | Return edges of a Delaunay triangulation, plus duplicate-point links. | Time: O(n log n), where n is the number of points; the divide-and-conquer construction is deterministic. This counts integer arithmetic operations, whose bit cost depends on coordinate magnitudes. |

### `rational.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `Point` | class | `Point(x: Rational \| int, y: Rational \| int)` | 2D point with rational coordinates. | Space: O(1) |
| `argsort` | function | `argsort(points: list[Point]) -> list[Point]` | Sort points by angle around the origin. | Time: O(n log n), where n is the number of points |
| `convex_hull` | function | `convex_hull(points: list[Point]) -> list[int]` | Compute the convex hull of a set of 2D points. | Time: O(n log n), where n is the number of points |
| `Circle` | class | `Circle(center: Point, radius: Rational \| int)` | Circle with rational center coordinates and radius. | Space: O(1) |
| `circumcircle` | function | `circumcircle(points: list[Point]) -> Circle` | Compute the circumcircle of 1-3 points. | Time: O(1) |
| `minimum_enclosing_circle` | function | `minimum_enclosing_circle(points: list[Point]) -> Circle` | Find the minimum enclosing circle of a set of 2D points. | Time: Expected O(n) rational operations, where n is the number of points |
| `Segment` | class | `Segment(start: Point, end: Point)` | Directed line segment on rational coordinates. | Space: O(1) |
