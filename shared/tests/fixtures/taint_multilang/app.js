// Source -> sink taint flow: untrusted request input reaches eval().
// A single-pattern matcher only sees eval(code); a taint engine proves `code`
// originates from req.query (the untrusted source).
function handler(req, res) {
  const userInput = req.query.expr;
  const code = userInput;
  res.send(eval(code));
}

module.exports = { handler };
