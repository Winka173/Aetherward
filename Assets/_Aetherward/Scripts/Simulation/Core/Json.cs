using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Aetherward.Sim.Core
{
    public enum JsonKind
    {
        Null,
        Bool,
        Number,
        String,
        Array,
        Object
    }

    /// <summary>
    /// Small allocation-tolerant JSON DOM used for content and save files. Content is parsed once at
    /// boot, so clarity beats speed here. Reflection-free to stay IL2CPP friendly.
    /// </summary>
    public sealed class JsonNode
    {
        public static readonly JsonNode Null = new JsonNode(JsonKind.Null);

        public JsonKind Kind { get; }
        private readonly bool _bool;
        private readonly double _number;
        private readonly string _string;
        private readonly List<JsonNode> _array;
        private readonly Dictionary<string, JsonNode> _object;
        private readonly List<string> _keyOrder;

        private JsonNode(JsonKind kind)
        {
            Kind = kind;
            if (kind == JsonKind.Array) _array = new List<JsonNode>();
            if (kind == JsonKind.Object)
            {
                _object = new Dictionary<string, JsonNode>(StringComparer.Ordinal);
                _keyOrder = new List<string>();
            }
        }

        private JsonNode(bool value) : this(JsonKind.Bool) { _bool = value; }
        private JsonNode(double value) : this(JsonKind.Number) { _number = value; }
        private JsonNode(string value) : this(JsonKind.String) { _string = value; }

        public static JsonNode NewObject() => new JsonNode(JsonKind.Object);
        public static JsonNode NewArray() => new JsonNode(JsonKind.Array);
        public static JsonNode From(bool v) => new JsonNode(v);
        public static JsonNode From(double v) => new JsonNode(v);
        public static JsonNode From(string v) => v == null ? Null : new JsonNode(v);

        public bool IsNull => Kind == JsonKind.Null;
        public int Count => Kind == JsonKind.Array ? _array.Count : (Kind == JsonKind.Object ? _object.Count : 0);
        public IReadOnlyList<JsonNode> Items => _array ?? (IReadOnlyList<JsonNode>)Array.Empty<JsonNode>();
        public IReadOnlyList<string> Keys => _keyOrder ?? (IReadOnlyList<string>)Array.Empty<string>();

        public JsonNode this[string key]
        {
            get
            {
                if (Kind != JsonKind.Object) return Null;
                return _object.TryGetValue(key, out JsonNode v) ? v : Null;
            }
        }

        public JsonNode this[int index]
        {
            get
            {
                if (Kind != JsonKind.Array || index < 0 || index >= _array.Count) return Null;
                return _array[index];
            }
        }

        public bool Has(string key) => Kind == JsonKind.Object && _object.ContainsKey(key);

        public JsonNode Set(string key, JsonNode value)
        {
            if (Kind != JsonKind.Object) throw new InvalidOperationException("Set on non-object");
            if (!_object.ContainsKey(key)) _keyOrder.Add(key);
            _object[key] = value ?? Null;
            return this;
        }

        public JsonNode Set(string key, string value) => Set(key, From(value));
        public JsonNode Set(string key, double value) => Set(key, From(value));
        public JsonNode Set(string key, bool value) => Set(key, From(value));

        public JsonNode Add(JsonNode value)
        {
            if (Kind != JsonKind.Array) throw new InvalidOperationException("Add on non-array");
            _array.Add(value ?? Null);
            return this;
        }

        public string AsString(string fallback = null) => Kind == JsonKind.String ? _string : (Kind == JsonKind.Number ? _number.ToString(CultureInfo.InvariantCulture) : fallback);
        public double AsDouble(double fallback = 0) => Kind == JsonKind.Number ? _number : fallback;
        public float AsFloat(float fallback = 0f) => Kind == JsonKind.Number ? (float)_number : fallback;
        public int AsInt(int fallback = 0) => Kind == JsonKind.Number ? (int)Math.Round(_number) : fallback;
        public long AsLong(long fallback = 0) => Kind == JsonKind.Number ? (long)Math.Round(_number) : fallback;
        public bool AsBool(bool fallback = false) => Kind == JsonKind.Bool ? _bool : fallback;

        public string Str(string key, string fallback = null) => this[key].AsString(fallback);
        public float Float(string key, float fallback = 0f) => this[key].AsFloat(fallback);
        public int Int(string key, int fallback = 0) => this[key].AsInt(fallback);
        public bool Bool(string key, bool fallback = false) => this[key].AsBool(fallback);

        public List<string> StringList(string key)
        {
            var result = new List<string>();
            foreach (JsonNode n in this[key].Items)
            {
                string s = n.AsString();
                if (s != null) result.Add(s);
            }
            return result;
        }

        // ------------------------------------------------------------------ parse

        public static JsonNode Parse(string text)
        {
            if (text == null) throw new ArgumentNullException(nameof(text));
            var parser = new Parser(text);
            parser.SkipWhitespace();
            JsonNode node = parser.ParseValue();
            parser.SkipWhitespace();
            if (!parser.AtEnd) throw parser.Error("Trailing characters after JSON value");
            return node;
        }

        private sealed class Parser
        {
            private readonly string _s;
            private int _i;

            public Parser(string s) { _s = s; }
            public bool AtEnd => _i >= _s.Length;

            public FormatException Error(string message)
            {
                int line = 1, col = 1;
                for (int k = 0; k < _i && k < _s.Length; k++)
                {
                    if (_s[k] == '\n') { line++; col = 1; } else col++;
                }
                return new FormatException(message + " at line " + line + ", column " + col);
            }

            public void SkipWhitespace()
            {
                while (_i < _s.Length)
                {
                    char c = _s[_i];
                    if (c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '﻿') { _i++; continue; }
                    // Content files allow // line comments for designer notes.
                    if (c == '/' && _i + 1 < _s.Length && _s[_i + 1] == '/')
                    {
                        while (_i < _s.Length && _s[_i] != '\n') _i++;
                        continue;
                    }
                    break;
                }
            }

            public JsonNode ParseValue()
            {
                if (AtEnd) throw Error("Unexpected end of JSON");
                char c = _s[_i];
                switch (c)
                {
                    case '{': return ParseObject();
                    case '[': return ParseArray();
                    case '"': return new JsonNode(ParseString());
                    case 't': Expect("true"); return new JsonNode(true);
                    case 'f': Expect("false"); return new JsonNode(false);
                    case 'n': Expect("null"); return Null;
                    default:
                        if (c == '-' || (c >= '0' && c <= '9')) return ParseNumber();
                        throw Error("Unexpected character '" + c + "'");
                }
            }

            private void Expect(string word)
            {
                if (string.CompareOrdinal(_s, _i, word, 0, word.Length) != 0) throw Error("Expected '" + word + "'");
                _i += word.Length;
            }

            private JsonNode ParseObject()
            {
                var node = new JsonNode(JsonKind.Object);
                _i++;
                SkipWhitespace();
                if (!AtEnd && _s[_i] == '}') { _i++; return node; }
                while (true)
                {
                    SkipWhitespace();
                    if (AtEnd || _s[_i] != '"') throw Error("Expected object key");
                    string key = ParseString();
                    SkipWhitespace();
                    if (AtEnd || _s[_i] != ':') throw Error("Expected ':'");
                    _i++;
                    SkipWhitespace();
                    JsonNode value = ParseValue();
                    if (node._object.ContainsKey(key)) throw Error("Duplicate key '" + key + "'");
                    node.Set(key, value);
                    SkipWhitespace();
                    if (AtEnd) throw Error("Unterminated object");
                    if (_s[_i] == ',')
                    {
                        _i++;
                        SkipWhitespace();
                        if (!AtEnd && _s[_i] == '}') { _i++; return node; } // tolerate trailing comma
                        continue;
                    }
                    if (_s[_i] == '}') { _i++; return node; }
                    throw Error("Expected ',' or '}'");
                }
            }

            private JsonNode ParseArray()
            {
                var node = new JsonNode(JsonKind.Array);
                _i++;
                SkipWhitespace();
                if (!AtEnd && _s[_i] == ']') { _i++; return node; }
                while (true)
                {
                    SkipWhitespace();
                    node._array.Add(ParseValue());
                    SkipWhitespace();
                    if (AtEnd) throw Error("Unterminated array");
                    if (_s[_i] == ',')
                    {
                        _i++;
                        SkipWhitespace();
                        if (!AtEnd && _s[_i] == ']') { _i++; return node; }
                        continue;
                    }
                    if (_s[_i] == ']') { _i++; return node; }
                    throw Error("Expected ',' or ']'");
                }
            }

            private string ParseString()
            {
                _i++;
                var sb = new StringBuilder();
                while (true)
                {
                    if (AtEnd) throw Error("Unterminated string");
                    char c = _s[_i++];
                    if (c == '"') return sb.ToString();
                    if (c != '\\') { sb.Append(c); continue; }
                    if (AtEnd) throw Error("Bad escape");
                    char e = _s[_i++];
                    switch (e)
                    {
                        case '"': sb.Append('"'); break;
                        case '\\': sb.Append('\\'); break;
                        case '/': sb.Append('/'); break;
                        case 'b': sb.Append('\b'); break;
                        case 'f': sb.Append('\f'); break;
                        case 'n': sb.Append('\n'); break;
                        case 'r': sb.Append('\r'); break;
                        case 't': sb.Append('\t'); break;
                        case 'u':
                            if (_i + 4 > _s.Length) throw Error("Bad unicode escape");
                            sb.Append((char)int.Parse(_s.Substring(_i, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                            _i += 4;
                            break;
                        default: throw Error("Unknown escape \\" + e);
                    }
                }
            }

            private JsonNode ParseNumber()
            {
                int start = _i;
                if (_s[_i] == '-') _i++;
                while (_i < _s.Length)
                {
                    char c = _s[_i];
                    if ((c >= '0' && c <= '9') || c == '.' || c == 'e' || c == 'E' || c == '+' || c == '-') _i++;
                    else break;
                }
                string token = _s.Substring(start, _i - start);
                if (!double.TryParse(token, NumberStyles.Float, CultureInfo.InvariantCulture, out double value))
                    throw Error("Invalid number '" + token + "'");
                return new JsonNode(value);
            }
        }

        // ------------------------------------------------------------------ write

        public string ToJson(bool pretty = false)
        {
            var sb = new StringBuilder();
            Write(sb, pretty, 0);
            return sb.ToString();
        }

        private void Write(StringBuilder sb, bool pretty, int depth)
        {
            switch (Kind)
            {
                case JsonKind.Null: sb.Append("null"); break;
                case JsonKind.Bool: sb.Append(_bool ? "true" : "false"); break;
                case JsonKind.Number: sb.Append(_number.ToString("R", CultureInfo.InvariantCulture)); break;
                case JsonKind.String: WriteString(sb, _string); break;
                case JsonKind.Array:
                    sb.Append('[');
                    for (int i = 0; i < _array.Count; i++)
                    {
                        if (i > 0) sb.Append(',');
                        if (pretty) NewLine(sb, depth + 1);
                        _array[i].Write(sb, pretty, depth + 1);
                    }
                    if (pretty && _array.Count > 0) NewLine(sb, depth);
                    sb.Append(']');
                    break;
                case JsonKind.Object:
                    sb.Append('{');
                    for (int i = 0; i < _keyOrder.Count; i++)
                    {
                        if (i > 0) sb.Append(',');
                        if (pretty) NewLine(sb, depth + 1);
                        WriteString(sb, _keyOrder[i]);
                        sb.Append(pretty ? ": " : ":");
                        _object[_keyOrder[i]].Write(sb, pretty, depth + 1);
                    }
                    if (pretty && _keyOrder.Count > 0) NewLine(sb, depth);
                    sb.Append('}');
                    break;
            }
        }

        private static void NewLine(StringBuilder sb, int depth)
        {
            sb.Append('\n');
            sb.Append(' ', depth * 2);
        }

        private static void WriteString(StringBuilder sb, string s)
        {
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
        }
    }
}
