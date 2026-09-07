# An Intuitive Explanation of Lambda Calculus

Lambda calculus is easiest to understand as a **tiny programming
language where everything is built out of functions**.

Despite having almost nothing in it, lambda calculus is powerful enough
to express essentially any computation a normal programming language can
perform. It's one of the theoretical foundations of functional
programming and computer science.

## 1. Start with an ordinary function

Suppose you have:

$$
f(x)=x+1
$$

Lambda calculus asks: why bother giving the function a name like $f$? We
can simply write the function itself:

$$
\lambda x.\;x+1
$$

Read this as:

> "A function that takes $x$ and returns $x+1$."

The symbol $\lambda$ basically means **"here comes an anonymous
function."**

In Python, the corresponding idea is:

``` python
lambda x: x + 1
```

So this notation isn't as exotic as it first looks.

## 2. Applying a function

If we want to apply

$$
\lambda x.\;x+1
$$

to $5$, we write:

$$
(\lambda x.\;x+1)\;5
$$

The intuitive rule is extremely simple:

> Replace $x$ with $5$.

So it becomes $5+1$, and therefore $6$.

This replacement process is called **beta reduction**.

## 3. The surprising part: pure lambda calculus has almost nothing else

Strictly speaking, pure lambda calculus doesn't even start with numbers,
addition, `if` statements, loops, or Boolean values.

It has only three kinds of expressions:

-   $x$ --- a variable
-   $\lambda x.M$ --- a function
-   $M\;N$ --- applying one expression to another

That's basically the entire language.

The astonishing result is that **this is enough to represent arbitrary
computation**.

## 4. Functions can consume functions

Consider:

$$
\lambda f.\lambda x.f\;x
$$

It means:

> Take a function $f$. Then take a value $x$. Apply $f$ to $x$.

For example, imagine:

$$
f = \lambda y.y+1
$$

Then applying the expression to $f$ and $5$ eventually gives $f(5)=6$.

This ability to treat functions just like ordinary values is the central
idea.

You can **pass a function into another function, return a function from
a function, and even use functions to represent data**.

## 5. Here's where it gets clever: numbers can be functions

Lambda calculus can represent the number $2$ as:

$$
\lambda f.\lambda x.f(f(x))
$$

Why would that mean 2?

Think of a number as answering the question:

> **How many times should I perform an operation?**

Thus:

$$
0 = \lambda f.\lambda x.x
$$

means apply $f$ zero times.

$$
1 = \lambda f.\lambda x.f(x)
$$

means apply it once.

$$
2 = \lambda f.\lambda x.f(f(x))
$$

means apply it twice.

$$
3 = \lambda f.\lambda x.f(f(f(x)))
$$

means apply it three times.

These are called **Church numerals**, after Alonzo Church, who developed
lambda calculus in the 1930s.

For instance, if $f(x)=x+10$, then Church numeral 3 gives:

$$
f(f(f(0))) = 30.
$$

The lambda expression itself doesn't know anything about the number 3 in
the conventional sense. **"Three" is encoded as doing something three
times.**

## 6. Even TRUE and FALSE can be functions

Define:

$$
TRUE = \lambda x.\lambda y.x
$$

and

$$
FALSE = \lambda x.\lambda y.y
$$

`TRUE` means: given two things, choose the first one. `FALSE` means:
given two things, choose the second one.

Now an `if` expression becomes:

$$
IF = \lambda b.\lambda x.\lambda y.b\;x\;y
$$

Then:

$$
IF\;TRUE\;A\;B \rightarrow A
$$

and:

$$
IF\;FALSE\;A\;B \rightarrow B.
$$

So we have effectively invented Boolean logic using **nothing but
functions**.

## The big idea

Lambda calculus isn't really interesting because it's a convenient way
to write programs. It's interesting because it asks a much deeper
question:

> **What are the minimum ingredients necessary for computation?**

And gives a remarkable answer:

$$
\boxed{\text{functions + variables + function application}}
$$

are enough.

Numbers can be represented by functions. Booleans can be represented by
functions. Data structures can be represented by functions. Recursion
can even be constructed from functions.

That's why lambda calculus can initially feel like someone saying
**"everything is a function"** and then taking that idea absurdly
seriously---until you discover that it actually works.

If you're learning this for a CS/theory course, the next important
concept is **beta reduction and variable substitution**, especially the
subtle difference between **free and bound variables**.
