const express = require('express');
const cors = require('cors');
const multer = require('multer');
const fetch = require('node-fetch');
const FormData = require('form-data');

const app = express();
app.use(cors());
const upload = multer();

const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbyCi-LjCMfE6aSch_1RMA4KI7g8KRrP_4RKfmx_1ihPCeiWhJ49Jn3F1dTCagSPVQGl9w/exec';

app.post('/upload', upload.single('file'), async (req, res) => {
  try {
    const form = new FormData();
    form.append('sku', req.body.sku);
    form.append('file', req.file.buffer, req.file.originalname);

    const response = await fetch(GOOGLE_SCRIPT_URL, {
      method: 'POST',
      body: form,
    });

    const text = await response.text();
    res.status(response.status).send(text);
  } catch (err) {
    res.status(500).json({ error: 'Proxy error', details: err.message });
  }
});

app.get('/', (req, res) => {
  res.send('Proxy funcionando');
});

module.exports = app;