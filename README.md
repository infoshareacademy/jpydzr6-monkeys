# jpydzr6-monkeys

# Monetary class

This is a class for basic monetary/money operations. In its core it operates in the smallest unit of a currency (called
minor unit).

The class is inspired by dinero.js library [dinero.js v2](https://v2.dinerojs.com/docs) library and its
fork [wilfredinni/dinero](https://wilfredinni.github.io/dinero/)

## Currencies

The class functions expects as the second argument a dictionary of specific currency. In the beginning there are
attached three currencies.

## Instantiating a monetary objects and allowed operations

- Instantiating
  ```
  pln1 = Monetary(1, PLN)
  pln2 = Monetary(Monetary.major_to_minor_unit(100.0, PLN), PLN)
  ```
  `m1 = PLN 0.01, m2 = PLN 100.00`
- Adding `pln3 = pln1 + pln2`
- Subtracting `pln3 = pln2 - pln1`
- Multiplying `pln3 = pln2 * 2` (the Monetary object must be on the left side of equation)
- Dividing `pln3 = pln2 / 2` (the Monetary object must be on the left side of equation)
- The result of division result is rounded. If it is less than the minor unit, the result will be zero `pln3 = pln1 / 2`
- Combining currencies will result in error
  ```
  eur1 = Monetary(100, EUR)
  some = pln1 + eur1
  ```
  *AttributeError: The currencies does not match*

## Major to minor unit conversion

If there is a need it is possible to convert major unit (typed as int, float or string) to the minor one of chosen
currency

- `Monetary.major_to_minor_unit(1, PLN)` will give in result (int) `100`
- `Monetary.major_to_minor_unit(1.11, PLN)` will give in result (int) `111`
- `Monetary.major_to_minor_unit(1.2, PLN)` will give in result (int) `120`
- `Monetary.major_to_minor_unit("1.34", PLN)` will give in result (int) `134`
- `Monetary.major_to_minor_unit("1.567", PLN)` will give in result (int) `156`