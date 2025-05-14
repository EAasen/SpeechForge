import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import {
  Container, Box, Typography, TextField, Button, Select, MenuItem, Snackbar, Alert, AppBar, Toolbar, IconButton, InputLabel, FormControl, Grid, LinearProgress, List, ListItem, ListItemText, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip, Checkbox, Dialog, DialogTitle, DialogContent, DialogActions, Slider
} from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import DownloadIcon from '@mui/icons-material/Download';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { WaveSurfer, WaveForm } from 'wavesurfer-react';
import WaveSurferCore from 'wavesurfer.js';
import TablePagination from '@mui/material/TablePagination';
import GetAppIcon from '@mui/icons-material/GetApp';
import SaveIcon from '@mui/icons-material/Save';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import HistoryIcon from '@mui/icons-material/History';
import CloudQueueIcon from '@mui/icons-material/CloudQueue';
import DeleteForeverIcon from '@mui/icons-material/DeleteForever';
import { useTranslation, initReactI18next } from 'react-i18next';
import i18n from 'i18next';
import AdminPanel from './AdminPanel'; // New admin panel component
import PreferencesDialog from './PreferencesDialog';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// i18n initialization
if (!i18n.isInitialized) {
  i18n
    .use(initReactI18next)
    .init({
      resources: {
        en: {
          translation: {
            'Login': 'Login',
            'Username': 'Username',
            'Password': 'Password',
            'Text-to-Speech': 'Text-to-Speech',
            'Text to Synthesize': 'Text to Synthesize',
            'Format': 'Format',
            'Quality': 'Quality',
            'Voice': 'Voice',
            'Speed': 'Speed',
            'Pitch': 'Pitch',
            'Tone': 'Tone',
            'Prompt': 'Prompt',
            'Speak': 'Speak',
            'Download Audio': 'Download Audio',
            'File Upload & Batch Processing': 'File Upload & Batch Processing',
            'Process Files': 'Process Files',
            'Async TTS Job Dashboard': 'Async TTS Job Dashboard',
            'Submit Async Job': 'Submit Async Job',
            'Catalog': 'Catalog',
            'Title': 'Title',
            'User': 'User',
            'Tenant': 'Tenant',
            'Date': 'Date',
            'Actions': 'Actions',
            'Delete Selected': 'Delete Selected',
            'Export CSV': 'Export CSV',
            'Batch Download': 'Batch Download',
            'Batch Export': 'Batch Export',
            'Batch Edit': 'Batch Edit',
            'Cloud Files': 'Cloud Files',
            'Download': 'Download',
            'Back': 'Back',
            'Load More': 'Load More',
            'Job History': 'Job History',
            'Result': 'Result',
            'Status': 'Status',
            'Submitted': 'Submitted',
            'Completed': 'Completed',
            'Error': 'Error',
            'Preferences': 'Preferences',
            'Language': 'Language',
            'Dark Theme': 'Dark Theme',
            'Notifications': 'Notifications',
            'Enable notifications for job completion': 'Enable notifications for job completion',
            'Job complete': 'Job complete',
            'Your async TTS job has finished.': 'Your async TTS job has finished.',
            // ...add more as needed...
          }
        },
        es: {
          translation: {
            'Login': 'Iniciar sesión',
            'Username': 'Usuario',
            'Password': 'Contraseña',
            'Text-to-Speech': 'Texto a voz',
            'Text to Synthesize': 'Texto a sintetizar',
            'Format': 'Formato',
            'Quality': 'Calidad',
            'Voice': 'Voz',
            'Speed': 'Velocidad',
            'Pitch': 'Tono',
            'Tone': 'Entonación',
            'Prompt': 'Prompt',
            'Speak': 'Hablar',
            'Download Audio': 'Descargar audio',
            'File Upload & Batch Processing': 'Subida de archivos y procesamiento por lotes',
            'Process Files': 'Procesar archivos',
            'Async TTS Job Dashboard': 'Panel de trabajos TTS asíncronos',
            'Submit Async Job': 'Enviar trabajo asíncrono',
            'Catalog': 'Catálogo',
            'Title': 'Título',
            'User': 'Usuario',
            'Tenant': 'Inquilino',
            'Date': 'Fecha',
            'Actions': 'Acciones',
            'Delete Selected': 'Eliminar seleccionados',
            'Export CSV': 'Exportar CSV',
            'Batch Download': 'Descarga por lotes',
            'Batch Export': 'Exportar por lotes',
            'Batch Edit': 'Editar por lotes',
            'Cloud Files': 'Archivos en la nube',
            'Download': 'Descargar',
            'Back': 'Atrás',
            'Load More': 'Cargar más',
            'Job History': 'Historial de trabajos',
            'Result': 'Resultado',
            'Status': 'Estado',
            'Submitted': 'Enviado',
            'Completed': 'Completado',
            'Error': 'Error',
            'Logout': 'Cerrar sesión',
            // ...add more as needed...
          }
        },
        zh: { translation: {
          'Login': '登录', 'Username': '用户名', 'Password': '密码', 'Text-to-Speech': '文本转语音', 'Text to Synthesize': '要合成的文本', 'Format': '格式', 'Quality': '质量', 'Voice': '声音', 'Speed': '语速', 'Pitch': '音调', 'Tone': '语气', 'Prompt': '提示', 'Speak': '朗读', 'Download Audio': '下载音频', 'File Upload & Batch Processing': '文件上传与批量处理', 'Process Files': '处理文件', 'Async TTS Job Dashboard': '异步TTS任务面板', 'Submit Async Job': '提交异步任务', 'Catalog': '目录', 'Title': '标题', 'User': '用户', 'Tenant': '租户', 'Date': '日期', 'Actions': '操作', 'Delete Selected': '删除所选', 'Export CSV': '导出CSV', 'Batch Download': '批量下载', 'Batch Export': '批量导出', 'Batch Edit': '批量编辑', 'Cloud Files': '云文件', 'Download': '下载', 'Back': '返回', 'Load More': '加载更多', 'Job History': '任务历史', 'Result': '结果', 'Status': '状态', 'Submitted': '已提交', 'Completed': '已完成', 'Error': '错误', 'Logout': '登出' } },
        hi: { translation: {
          'Login': 'लॉगिन', 'Username': 'उपयोगकर्ता नाम', 'Password': 'पासवर्ड', 'Text-to-Speech': 'पाठ से वाक्', 'Text to Synthesize': 'सिंथेसाइज़ करने के लिए पाठ', 'Format': 'प्रारूप', 'Quality': 'गुणवत्ता', 'Voice': 'आवाज़', 'Speed': 'गति', 'Pitch': 'पिच', 'Tone': 'स्वर', 'Prompt': 'प्रॉम्प्ट', 'Speak': 'बोलें', 'Download Audio': 'ऑडियो डाउनलोड करें', 'File Upload & Batch Processing': 'फ़ाइल अपलोड और बैच प्रोसेसिंग', 'Process Files': 'फ़ाइलें प्रोसेस करें', 'Async TTS Job Dashboard': 'असिंक TTS जॉब डैशबोर्ड', 'Submit Async Job': 'असिंक जॉब सबमिट करें', 'Catalog': 'कैटलॉग', 'Title': 'शीर्षक', 'User': 'उपयोगकर्ता', 'Tenant': 'टेनेंट', 'Date': 'तारीख', 'Actions': 'क्रियाएँ', 'Delete Selected': 'चयनित हटाएँ', 'Export CSV': 'CSV निर्यात करें', 'Batch Download': 'बैच डाउनलोड', 'Batch Export': 'बैच निर्यात', 'Batch Edit': 'बैच संपादन', 'Cloud Files': 'क्लाउड फ़ाइलें', 'Download': 'डाउनलोड', 'Back': 'वापस', 'Load More': 'और लोड करें', 'Job History': 'जॉब इतिहास', 'Result': 'परिणाम', 'Status': 'स्थिति', 'Submitted': 'प्रस्तुत', 'Completed': 'पूर्ण', 'Error': 'त्रुटि', 'Logout': 'लॉगआउट' } },
        ar: { translation: {
          'Login': 'تسجيل الدخول', 'Username': 'اسم المستخدم', 'Password': 'كلمة المرور', 'Text-to-Speech': 'تحويل النص إلى كلام', 'Text to Synthesize': 'النص المراد تحويله', 'Format': 'الصيغة', 'Quality': 'الجودة', 'Voice': 'الصوت', 'Speed': 'السرعة', 'Pitch': 'النغمة', 'Tone': 'النبرة', 'Prompt': 'الموجه', 'Speak': 'تحدث', 'Download Audio': 'تحميل الصوت', 'File Upload & Batch Processing': 'رفع الملفات والمعالجة الدُفعية', 'Process Files': 'معالجة الملفات', 'Async TTS Job Dashboard': 'لوحة مهام TTS غير المتزامنة', 'Submit Async Job': 'إرسال مهمة غير متزامنة', 'Catalog': 'الفهرس', 'Title': 'العنوان', 'User': 'المستخدم', 'Tenant': 'المستأجر', 'Date': 'التاريخ', 'Actions': 'الإجراءات', 'Delete Selected': 'حذف المحدد', 'Export CSV': 'تصدير CSV', 'Batch Download': 'تنزيل دفعة', 'Batch Export': 'تصدير دفعة', 'Batch Edit': 'تعديل دفعة', 'Cloud Files': 'ملفات السحابة', 'Download': 'تحميل', 'Back': 'رجوع', 'Load More': 'تحميل المزيد', 'Job History': 'سجل المهام', 'Result': 'النتيجة', 'Status': 'الحالة', 'Submitted': 'تم الإرسال', 'Completed': 'مكتمل', 'Error': 'خطأ', 'Logout': 'تسجيل الخروج' } },
        fr: { translation: {
          'Login': 'Connexion', 'Username': 'Nom d’utilisateur', 'Password': 'Mot de passe', 'Text-to-Speech': 'Synthèse vocale', 'Text to Synthesize': 'Texte à synthétiser', 'Format': 'Format', 'Quality': 'Qualité', 'Voice': 'Voix', 'Speed': 'Vitesse', 'Pitch': 'Tonalité', 'Tone': 'Intonation', 'Prompt': 'Invite', 'Speak': 'Parler', 'Download Audio': 'Télécharger l’audio', 'File Upload & Batch Processing': 'Téléversement et traitement par lot', 'Process Files': 'Traiter les fichiers', 'Async TTS Job Dashboard': 'Tableau de bord TTS asynchrone', 'Submit Async Job': 'Soumettre une tâche asynchrone', 'Catalog': 'Catalogue', 'Title': 'Titre', 'User': 'Utilisateur', 'Tenant': 'Locataire', 'Date': 'Date', 'Actions': 'Actions', 'Delete Selected': 'Supprimer la sélection', 'Export CSV': 'Exporter CSV', 'Batch Download': 'Télécharger par lot', 'Batch Export': 'Exporter par lot', 'Batch Edit': 'Éditer par lot', 'Cloud Files': 'Fichiers cloud', 'Download': 'Télécharger', 'Back': 'Retour', 'Load More': 'Charger plus', 'Job History': 'Historique des tâches', 'Result': 'Résultat', 'Status': 'Statut', 'Submitted': 'Soumis', 'Completed': 'Terminé', 'Error': 'Erreur', 'Logout': 'Déconnexion' } },
        de: { translation: {
          'Login': 'Anmelden', 'Username': 'Benutzername', 'Password': 'Passwort', 'Text-to-Speech': 'Text-zu-Sprache', 'Text to Synthesize': 'Zu synthetisierender Text', 'Format': 'Format', 'Quality': 'Qualität', 'Voice': 'Stimme', 'Speed': 'Geschwindigkeit', 'Pitch': 'Tonhöhe', 'Tone': 'Ton', 'Prompt': 'Eingabeaufforderung', 'Speak': 'Sprechen', 'Download Audio': 'Audio herunterladen', 'File Upload & Batch Processing': 'Datei-Upload & Stapelverarbeitung', 'Process Files': 'Dateien verarbeiten', 'Async TTS Job Dashboard': 'Asynchrones TTS-Dashboard', 'Submit Async Job': 'Asynchronen Job absenden', 'Catalog': 'Katalog', 'Title': 'Titel', 'User': 'Benutzer', 'Tenant': 'Mandant', 'Date': 'Datum', 'Actions': 'Aktionen', 'Delete Selected': 'Ausgewählte löschen', 'Export CSV': 'CSV exportieren', 'Batch Download': 'Stapel-Download', 'Batch Export': 'Stapel-Export', 'Batch Edit': 'Stapel-Bearbeitung', 'Cloud Files': 'Cloud-Dateien', 'Download': 'Herunterladen', 'Back': 'Zurück', 'Load More': 'Mehr laden', 'Job History': 'Jobverlauf', 'Result': 'Ergebnis', 'Status': 'Status', 'Submitted': 'Eingereicht', 'Completed': 'Abgeschlossen', 'Error': 'Fehler', 'Logout': 'Abmelden' } },
        pt: { translation: {
          'Login': 'Entrar', 'Username': 'Usuário', 'Password': 'Senha', 'Text-to-Speech': 'Texto para fala', 'Text to Synthesize': 'Texto para sintetizar', 'Format': 'Formato', 'Quality': 'Qualidade', 'Voice': 'Voz', 'Speed': 'Velocidade', 'Pitch': 'Tom', 'Tone': 'Entonação', 'Prompt': 'Prompt', 'Speak': 'Falar', 'Download Audio': 'Baixar áudio', 'File Upload & Batch Processing': 'Upload de arquivos & processamento em lote', 'Process Files': 'Processar arquivos', 'Async TTS Job Dashboard': 'Painel de tarefas TTS assíncronas', 'Submit Async Job': 'Enviar tarefa assíncrona', 'Catalog': 'Catálogo', 'Title': 'Título', 'User': 'Usuário', 'Tenant': 'Locatário', 'Date': 'Data', 'Actions': 'Ações', 'Delete Selected': 'Excluir selecionados', 'Export CSV': 'Exportar CSV', 'Batch Download': 'Baixar em lote', 'Batch Export': 'Exportar em lote', 'Batch Edit': 'Editar em lote', 'Cloud Files': 'Arquivos na nuvem', 'Download': 'Baixar', 'Back': 'Voltar', 'Load More': 'Carregar mais', 'Job History': 'Histórico de tarefas', 'Result': 'Resultado', 'Status': 'Status', 'Submitted': 'Enviado', 'Completed': 'Concluído', 'Error': 'Erro', 'Logout': 'Sair' } },
        bn: { translation: {
          'Login': 'লগইন', 'Username': 'ব্যবহারকারীর নাম', 'Password': 'পাসওয়ার্ড', 'Text-to-Speech': 'টেক্সট-টু-স্পিচ', 'Text to Synthesize': 'সিন্থেসাইজ করার জন্য টেক্সট', 'Format': 'ফরম্যাট', 'Quality': 'গুণমান', 'Voice': 'ভয়েস', 'Speed': 'গতি', 'Pitch': 'পিচ', 'Tone': 'টোন', 'Prompt': 'প্রম্পট', 'Speak': 'বলুন', 'Download Audio': 'অডিও ডাউনলোড করুন', 'File Upload & Batch Processing': 'ফাইল আপলোড ও ব্যাচ প্রসেসিং', 'Process Files': 'ফাইল প্রসেস করুন', 'Async TTS Job Dashboard': 'অ্যাসিঙ্ক টি.টি.এস. জব ড্যাশবোর্ড', 'Submit Async Job': 'অ্যাসিঙ্ক জব জমা দিন', 'Catalog': 'ক্যাটালগ', 'Title': 'শিরোনাম', 'User': 'ব্যবহারকারী', 'Tenant': 'টেন্যান্ট', 'Date': 'তারিখ', 'Actions': 'কর্ম', 'Delete Selected': 'নির্বাচিত মুছুন', 'Export CSV': 'CSV এক্সপোর্ট করুন', 'Batch Download': 'ব্যাচ ডাউনলোড', 'Batch Export': 'ব্যাচ এক্সপোর্ট', 'Batch Edit': 'ব্যাচ এডিট', 'Cloud Files': 'ক্লাউড ফাইল', 'Download': 'ডাউনলোড', 'Back': 'ফিরে যান', 'Load More': 'আরো লোড করুন', 'Job History': 'জব ইতিহাস', 'Result': 'ফলাফল', 'Status': 'স্ট্যাটাস', 'Submitted': 'জমা', 'Completed': 'সম্পন্ন', 'Error': 'ত্রুটি', 'Logout': 'লগআউট' } },
        ru: { translation: {
          'Login': 'Войти', 'Username': 'Имя пользователя', 'Password': 'Пароль', 'Text-to-Speech': 'Текст в речь', 'Text to Synthesize': 'Текст для синтеза', 'Format': 'Формат', 'Quality': 'Качество', 'Voice': 'Голос', 'Speed': 'Скорость', 'Pitch': 'Высота', 'Tone': 'Тон', 'Prompt': 'Подсказка', 'Speak': 'Говорить', 'Download Audio': 'Скачать аудио', 'File Upload & Batch Processing': 'Загрузка файлов и пакетная обработка', 'Process Files': 'Обработать файлы', 'Async TTS Job Dashboard': 'Панель асинхронных задач TTS', 'Submit Async Job': 'Отправить асинхронную задачу', 'Catalog': 'Каталог', 'Title': 'Название', 'User': 'Пользователь', 'Tenant': 'Арендатор', 'Date': 'Дата', 'Actions': 'Действия', 'Delete Selected': 'Удалить выбранное', 'Export CSV': 'Экспорт CSV', 'Batch Download': 'Пакетная загрузка', 'Batch Export': 'Пакетный экспорт', 'Batch Edit': 'Пакетное редактирование', 'Cloud Files': 'Файлы в облаке', 'Download': 'Скачать', 'Back': 'Назад', 'Load More': 'Загрузить еще', 'Job History': 'История задач', 'Result': 'Результат', 'Status': 'Статус', 'Submitted': 'Отправлено', 'Completed': 'Завершено', 'Error': 'Ошибка', 'Logout': 'Выйти' } },
        ja: { translation: {
          'Login': 'ログイン', 'Username': 'ユーザー名', 'Password': 'パスワード', 'Text-to-Speech': 'テキスト読み上げ', 'Text to Synthesize': '合成するテキスト', 'Format': 'フォーマット', 'Quality': '品質', 'Voice': '声', 'Speed': '速度', 'Pitch': 'ピッチ', 'Tone': 'トーン', 'Prompt': 'プロンプト', 'Speak': '話す', 'Download Audio': '音声をダウンロード', 'File Upload & Batch Processing': 'ファイルアップロードとバッチ処理', 'Process Files': 'ファイルを処理', 'Async TTS Job Dashboard': '非同期TTSジョブダッシュボード', 'Submit Async Job': '非同期ジョブを送信', 'Catalog': 'カタログ', 'Title': 'タイトル', 'User': 'ユーザー', 'Tenant': 'テナント', 'Date': '日付', 'Actions': '操作', 'Delete Selected': '選択を削除', 'Export CSV': 'CSVエクスポート', 'Batch Download': 'バッチダウンロード', 'Batch Export': 'バッチエクスポート', 'Batch Edit': 'バッチ編集', 'Cloud Files': 'クラウドファイル', 'Download': 'ダウンロード', 'Back': '戻る', 'Load More': 'もっと読み込む', 'Job History': 'ジョブ履歴', 'Result': '結果', 'Status': 'ステータス', 'Submitted': '送信済み', 'Completed': '完了', 'Error': 'エラー', 'Logout': 'ログアウト' } },
        sv: { translation: {
          'Login': 'Logga in', 'Username': 'Användarnamn', 'Password': 'Lösenord', 'Text-to-Speech': 'Text till tal', 'Text to Synthesize': 'Text att syntetisera', 'Format': 'Format', 'Quality': 'Kvalitet', 'Voice': 'Röst', 'Speed': 'Hastighet', 'Pitch': 'Tonhöjd', 'Tone': 'Ton', 'Prompt': 'Prompt', 'Speak': 'Tala', 'Download Audio': 'Ladda ner ljud', 'File Upload & Batch Processing': 'Filuppladdning & batchbearbetning', 'Process Files': 'Bearbeta filer', 'Async TTS Job Dashboard': 'Asynkront TTS-panel', 'Submit Async Job': 'Skicka asynkront jobb', 'Catalog': 'Katalog', 'Title': 'Titel', 'User': 'Användare', 'Tenant': 'Hyresgäst', 'Date': 'Datum', 'Actions': 'Åtgärder', 'Delete Selected': 'Ta bort valda', 'Export CSV': 'Eksportera CSV', 'Batch Download': 'Batchnedladdning', 'Batch Export': 'Batcheksport', 'Batch Edit': 'Batchredigering', 'Cloud Files': 'Molnfiler', 'Download': 'Ladda ner', 'Back': 'Tillbaka', 'Load More': 'Ladda mer', 'Job History': 'Jobbhistorik', 'Result': 'Resultat', 'Status': 'Status', 'Submitted': 'Inskickad', 'Completed': 'Färdig', 'Error': 'Fel', 'Logout': 'Logga ut' } },
        no: { translation: {
          'Login': 'Logg inn', 'Username': 'Brukernavn', 'Password': 'Passord', 'Text-to-Speech': 'Tekst til tale', 'Text to Synthesize': 'Tekst å syntetisere', 'Format': 'Format', 'Quality': 'Kvalitet', 'Voice': 'Stemme', 'Speed': 'Hastighet', 'Pitch': 'Tonehøyde', 'Tone': 'Tone', 'Prompt': 'Prompt', 'Speak': 'Snakk', 'Download Audio': 'Last ned lyd', 'File Upload & Batch Processing': 'Filopplasting & batchbehandling', 'Process Files': 'Behandle filer', 'Async TTS Job Dashboard': 'Asynkron TTS-jobbpanel', 'Submit Async Job': 'Send asynkron jobb', 'Catalog': 'Katalog', 'Title': 'Tittel', 'User': 'Bruker', 'Tenant': 'Leietaker', 'Date': 'Dato', 'Actions': 'Handlinger', 'Delete Selected': 'Slett valgte', 'Export CSV': 'Eksporter CSV', 'Batch Download': 'Batchnedlasting', 'Batch Export': 'Batcheksport', 'Batch Edit': 'Batchredigering', 'Cloud Files': 'Skyfiler', 'Download': 'Last ned', 'Back': 'Tilbake', 'Load More': 'Last mer', 'Job History': 'Jobbhistorikk', 'Result': 'Resultat', 'Status': 'Status', 'Submitted': 'Sendt inn', 'Completed': 'Fullført', 'Error': 'Feil', 'Logout': 'Logg ut' } },
        da: { translation: {
          'Login': 'Log ind', 'Username': 'Brugernavn', 'Password': 'Adgangskode', 'Text-to-Speech': 'Tekst til tale', 'Text to Synthesize': 'Tekst til syntese', 'Format': 'Format', 'Quality': 'Kvalitet', 'Voice': 'Stemme', 'Speed': 'Hastighed', 'Pitch': 'Tonehøjde', 'Tone': 'Tone', 'Prompt': 'Prompt', 'Speak': 'Tal', 'Download Audio': 'Download lyd', 'File Upload & Batch Processing': 'Filupload & batchbehandling', 'Process Files': 'Behandl filer', 'Async TTS Job Dashboard': 'Asynkron TTS-jobdashboard', 'Submit Async Job': 'Indsend asynkront job', 'Catalog': 'Katalog', 'Title': 'Titel', 'User': 'Bruger', 'Tenant': 'Lejer', 'Date': 'Dato', 'Actions': 'Handlinger', 'Delete Selected': 'Slet valgte', 'Export CSV': 'Eksporter CSV', 'Batch Download': 'Batchdownload', 'Batch Export': 'Batcheksport', 'Batch Edit': 'Batchredigering', 'Cloud Files': 'Cloud-filer', 'Download': 'Download', 'Back': 'Tilbage', 'Load More': 'Indlæs mere', 'Job History': 'Jobhistorik', 'Result': 'Resultat', 'Status': 'Status', 'Submitted': 'Indsendt', 'Completed': 'Fuldført', 'Error': 'Fejl', 'Logout': 'Log ud' } },
        tr: { translation: {
          'Login': 'Giriş yap', 'Username': 'Kullanıcı adı', 'Password': 'Şifre', 'Text-to-Speech': 'Metinden sese', 'Text to Synthesize': 'Sentezlenecek metin', 'Format': 'Format', 'Quality': 'Kalite', 'Voice': 'Ses', 'Speed': 'Hız', 'Pitch': 'Perde', 'Tone': 'Ton', 'Prompt': 'Prompt', 'Speak': 'Konuş', 'Download Audio': 'Ses indir', 'File Upload & Batch Processing': 'Dosya yükleme & toplu işleme', 'Process Files': 'Dosyaları işle', 'Async TTS Job Dashboard': 'Asenkron TTS Görev Paneli', 'Submit Async Job': 'Asenkron Görev Gönder', 'Catalog': 'Katalog', 'Title': 'Başlık', 'User': 'Kullanıcı', 'Tenant': 'Kiralayan', 'Date': 'Tarih', 'Actions': 'Eylemler', 'Delete Selected': 'Seçileni sil', 'Export CSV': 'CSV dışa aktar', 'Batch Download': 'Toplu indir', 'Batch Export': 'Toplu dışa aktar', 'Batch Edit': 'Toplu düzenle', 'Cloud Files': 'Bulut dosyaları', 'Download': 'İndir', 'Back': 'Geri', 'Load More': 'Daha fazla yükle', 'Job History': 'Görev geçmişi', 'Result': 'Sonuç', 'Status': 'Durum', 'Submitted': 'Gönderildi', 'Completed': 'Tamamlandı', 'Error': 'Hata', 'Logout': 'Çıkış yap' } },
        it: { translation: {
          'Login': 'Accesso', 'Username': 'Nome utente', 'Password': 'Password', 'Text-to-Speech': 'Sintesi vocale', 'Text to Synthesize': 'Testo da sintetizzare', 'Format': 'Formato', 'Quality': 'Qualità', 'Voice': 'Voce', 'Speed': 'Velocità', 'Pitch': 'Intonazione', 'Tone': 'Tono', 'Prompt': 'Prompt', 'Speak': 'Parla', 'Download Audio': 'Scarica audio', 'File Upload & Batch Processing': 'Carica file & Elaborazione batch', 'Process Files': 'Elabora file', 'Async TTS Job Dashboard': 'Dashboard lavori TTS asincroni', 'Submit Async Job': 'Invia lavoro asincrono', 'Catalog': 'Catalogo', 'Title': 'Titolo', 'User': 'Utente', 'Tenant': 'Tenant', 'Date': 'Data', 'Actions': 'Azioni', 'Delete Selected': 'Elimina selezionati', 'Export CSV': 'Esporta CSV', 'Batch Download': 'Download batch', 'Batch Export': 'Esporta batch', 'Batch Edit': 'Modifica batch', 'Cloud Files': 'File cloud', 'Download': 'Scarica', 'Back': 'Indietro', 'Load More': 'Carica altro', 'Job History': 'Storico lavori', 'Result': 'Risultato', 'Status': 'Stato', 'Submitted': 'Inviato', 'Completed': 'Completato', 'Error': 'Errore', 'Logout': 'Disconnetti', 'Admin Panel': 'Pannello Admin', 'Users': 'Utenti', 'Tenants': 'Tenant', 'Audit Log': 'Registro audit', 'Edit': 'Modifica', 'Delete': 'Elimina', 'Add User': 'Aggiungi utente', 'Edit User': 'Modifica utente', 'Save': 'Salva', 'Cancel': 'Annulla', 'User saved': 'Utente salvato', 'Failed to save user': 'Salvataggio utente fallito', 'User deleted': 'Utente eliminato', 'Failed to delete user': 'Eliminazione utente fallita', 'Timestamp': 'Data/ora', 'Action': 'Azione', 'Details': 'Dettagli', 'Success': 'Successo', 'Play': 'Riproduci', 'Audio': 'Audio', 'untitled': 'senza titolo'
        }},
        ko: { translation: {
          'Login': '로그인', 'Username': '사용자 이름', 'Password': '비밀번호', 'Text-to-Speech': '음성 합성', 'Text to Synthesize': '합성할 텍스트', 'Format': '형식', 'Quality': '품질', 'Voice': '음성', 'Speed': '속도', 'Pitch': '피치', 'Tone': '톤', 'Prompt': '프롬프트', 'Speak': '말하기', 'Download Audio': '오디오 다운로드', 'File Upload & Batch Processing': '파일 업로드 & 일괄 처리', 'Process Files': '파일 처리', 'Async TTS Job Dashboard': '비동기 TTS 작업 대시보드', 'Submit Async Job': '비동기 작업 제출', 'Catalog': '카탈로그', 'Title': '제목', 'User': '사용자', 'Tenant': '테넌트', 'Date': '날짜', 'Actions': '작업', 'Delete Selected': '선택 삭제', 'Export CSV': 'CSV 내보내기', 'Batch Download': '일괄 다운로드', 'Batch Export': '일괄 내보내기', 'Batch Edit': '일괄 편집', 'Cloud Files': '클라우드 파일', 'Download': '다운로드', 'Back': '뒤로', 'Load More': '더 불러오기', 'Job History': '작업 기록', 'Result': '결과', 'Status': '상태', 'Submitted': '제출됨', 'Completed': '완료됨', 'Error': '오류', 'Logout': '로그아웃', 'Admin Panel': '관리자 패널', 'Users': '사용자', 'Tenants': '테넌트', 'Audit Log': '감사 로그', 'Edit': '수정', 'Delete': '삭제', 'Add User': '사용자 추가', 'Edit User': '사용자 수정', 'Save': '저장', 'Cancel': '취소', 'User saved': '사용자 저장됨', 'Failed to save user': '사용자 저장 실패', 'User deleted': '사용자 삭제됨', 'Failed to delete user': '사용자 삭제 실패', 'Timestamp': '타임스탬프', 'Action': '동작', 'Details': '세부정보', 'Success': '성공', 'Play': '재생', 'Audio': '오디오', 'untitled': '제목 없음'
        }},
        pl: { translation: {
          'Login': 'Logowanie', 'Username': 'Nazwa użytkownika', 'Password': 'Hasło', 'Text-to-Speech': 'Synteza mowy', 'Text to Synthesize': 'Tekst do syntezy', 'Format': 'Format', 'Quality': 'Jakość', 'Voice': 'Głos', 'Speed': 'Szybkość', 'Pitch': 'Ton', 'Tone': 'Barwa', 'Prompt': 'Prompt', 'Speak': 'Mów', 'Download Audio': 'Pobierz audio', 'File Upload & Batch Processing': 'Przesyłanie plików & przetwarzanie wsadowe', 'Process Files': 'Przetwarzaj pliki', 'Async TTS Job Dashboard': 'Panel zadań TTS asynchronicznych', 'Submit Async Job': 'Wyślij zadanie asynchroniczne', 'Catalog': 'Katalog', 'Title': 'Tytuł', 'User': 'Użytkownik', 'Tenant': 'Najemca', 'Date': 'Data', 'Actions': 'Akcje', 'Delete Selected': 'Usuń wybrane', 'Export CSV': 'Eksportuj CSV', 'Batch Download': 'Pobierz wsadowo', 'Batch Export': 'Eksportuj wsadowo', 'Batch Edit': 'Edytuj wsadowo', 'Cloud Files': 'Pliki w chmurze', 'Download': 'Pobierz', 'Back': 'Wstecz', 'Load More': 'Załaduj więcej', 'Job History': 'Historia zadań', 'Result': 'Wynik', 'Status': 'Status', 'Submitted': 'Wysłano', 'Completed': 'Zakończono', 'Error': 'Błąd', 'Logout': 'Wyloguj', 'Admin Panel': 'Panel administratora', 'Users': 'Użytkownicy', 'Tenants': 'Najemcy', 'Audit Log': 'Dziennik audytu', 'Edit': 'Edytuj', 'Delete': 'Usuń', 'Add User': 'Dodaj użytkownika', 'Edit User': 'Edytuj użytkownika', 'Save': 'Zapisz', 'Cancel': 'Anuluj', 'User saved': 'Użytkownik zapisany', 'Failed to save user': 'Nie udało się zapisać użytkownika', 'User deleted': 'Użytkownik usunięty', 'Failed to delete user': 'Nie udało się usunąć użytkownika', 'Timestamp': 'Znacznik czasu', 'Action': 'Akcja', 'Details': 'Szczegóły', 'Success': 'Sukces', 'Play': 'Odtwórz', 'Audio': 'Audio', 'untitled': 'bez tytułu'
        }},
        nl: { translation: {
          'Login': 'Inloggen', 'Username': 'Gebruikersnaam', 'Password': 'Wachtwoord', 'Text-to-Speech': 'Tekst-naar-spraak', 'Text to Synthesize': 'Tekst om te synthetiseren', 'Format': 'Formaat', 'Quality': 'Kwaliteit', 'Voice': 'Stem', 'Speed': 'Snelheid', 'Pitch': 'Toonhoogte', 'Tone': 'Toon', 'Prompt': 'Prompt', 'Speak': 'Spreek', 'Download Audio': 'Audio downloaden', 'File Upload & Batch Processing': 'Bestanden uploaden & batchverwerking', 'Process Files': 'Bestanden verwerken', 'Async TTS Job Dashboard': 'Async TTS Taakdashboard', 'Submit Async Job': 'Verzend asynchrone taak', 'Catalog': 'Catalogus', 'Title': 'Titel', 'User': 'Gebruiker', 'Tenant': 'Huurder', 'Date': 'Datum', 'Actions': 'Acties', 'Delete Selected': 'Verwijder geselecteerden', 'Export CSV': 'Exporteer CSV', 'Batch Download': 'Batch downloaden', 'Batch Export': 'Batch exporteren', 'Batch Edit': 'Batch bewerken', 'Cloud Files': 'Cloudbestanden', 'Download': 'Downloaden', 'Back': 'Terug', 'Load More': 'Meer laden', 'Job History': 'Taakgeschiedenis', 'Result': 'Resultaat', 'Status': 'Status', 'Submitted': 'Ingediend', 'Completed': 'Voltooid', 'Error': 'Fout', 'Logout': 'Uitloggen', 'Admin Panel': 'Beheerderpaneel', 'Users': 'Gebruikers', 'Tenants': 'Huurders', 'Audit Log': 'Auditlogboek', 'Edit': 'Bewerken', 'Delete': 'Verwijderen', 'Add User': 'Gebruiker toevoegen', 'Edit User': 'Gebruiker bewerken', 'Save': 'Opslaan', 'Cancel': 'Annuleren', 'User saved': 'Gebruiker opgeslagen', 'Failed to save user': 'Gebruiker opslaan mislukt', 'User deleted': 'Gebruiker verwijderd', 'Failed to delete user': 'Gebruiker verwijderen mislukt', 'Timestamp': 'Tijdstempel', 'Action': 'Actie', 'Details': 'Details', 'Success': 'Succes', 'Play': 'Afspelen', 'Audio': 'Audio', 'untitled': 'zonder titel'
        }},
        // ...add more languages as needed...
      },
      lng: 'en',
      fallbackLng: 'en',
      interpolation: { escapeValue: false }
    });
}

// Custom AudioPlayer component with waveform visualization
function AudioPlayer({ src }) {
  const wavesurferRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [ready, setReady] = useState(false);

  // WaveSurfer options
  const wsOptions = {
    waveColor: '#90caf9',
    progressColor: '#1976d2',
    cursorColor: '#1976d2',
    barWidth: 2,
    barRadius: 2,
    responsive: true,
    height: 60,
    normalize: true,
  };

  // Mount and event handlers
  const handleWSMount = ws => {
    if (ws) {
      wavesurferRef.current = ws;
      ws.load(src);
      ws.setPlaybackRate(speed);
      ws.on('ready', () => {
        setDuration(ws.getDuration());
        setReady(true);
      });
      ws.on('audioprocess', () => {
        setCurrentTime(ws.getCurrentTime());
      });
      ws.on('seek', progress => {
        const seekTime = progress * ws.getDuration();
        setCurrentTime(seekTime);
      });
      ws.on('finish', () => setPlaying(false));
    }
  };

  useEffect(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setPlaybackRate(speed);
    }
  }, [speed]);

  useEffect(() => {
    if (wavesurferRef.current) {
      if (playing) wavesurferRef.current.play();
      else wavesurferRef.current.pause();
    }
  }, [playing]);

  useEffect(() => {
    setPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setReady(false);
    if (wavesurferRef.current) {
      wavesurferRef.current.load(src);
    }
  }, [src]);

  const togglePlay = () => setPlaying(p => !p);
  const handleSeek = (e, val) => {
    if (wavesurferRef.current && duration) {
      wavesurferRef.current.seekTo(val / duration);
      setCurrentTime(val);
    }
  };
  const handleSpeed = (e) => setSpeed(e.target.value);
  const formatTime = (s) => {
    if (isNaN(s)) return '0:00';
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60).toString().padStart(2, '0');
    return `${m}:${sec}`;
  };

  return (
    <Box sx={{ width: '100%', mb: 1 }}>
      <WaveSurfer onMount={handleWSMount} options={{ ...wsOptions, url: src }}>
        <WaveForm />
      </WaveSurfer>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
        <Button onClick={togglePlay} size="small" variant="outlined">{playing ? 'Pause' : 'Play'}</Button>
        <Slider min={0} max={duration} value={currentTime} onChange={handleSeek} size="small" sx={{ flex: 1 }} />
        <Typography variant="caption">{formatTime(currentTime)} / {formatTime(duration)}</Typography>
        <Select value={speed} onChange={handleSpeed} size="small" sx={{ width: 70, ml: 1 }}>
          <MenuItem value={0.5}>0.5x</MenuItem>
          <MenuItem value={1}>1x</MenuItem>
          <MenuItem value={1.5}>1.5x</MenuItem>
          <MenuItem value={2}>2x</MenuItem>
        </Select>
      </Box>
    </Box>
  );
}

function LanguageSwitcher() {
  const { i18n } = useTranslation();
  return (
    <div style={{ display: 'inline-block', marginLeft: 16 }}>
      <label htmlFor="lang-select" style={{ marginRight: 4 }}>🌐</label>
      <select
        id="lang-select"
        value={i18n.language}
        onChange={e => i18n.changeLanguage(e.target.value)}
        aria-label="Select language"
      >
        <option value="en">English</option>
        <option value="zh">中文</option>
        <option value="es">Español</option>
        <option value="hi">हिन्दी</option>
        <option value="ar">العربية</option>
        <option value="fr">Français</option>
        <option value="de">Deutsch</option>
        <option value="pt">Português</option>
        <option value="bn">বাংলা</option>
        <option value="ru">Русский</option>
        <option value="ja">日本語</option>
        <option value="sv">Svenska</option>
        <option value="no">Norsk</option>
        <option value="da">Dansk</option>
        <option value="tr">Türkçe</option>
        <option value="it">Italiano</option>
        <option value="ko">한국어</option>
        <option value="pl">Polski</option>
        <option value="nl">Nederlands</option>
      </select>
    </div>
  );
}

function App() {
  const { t } = useTranslation();
  const [text, setText] = useState('');
  const [token, setToken] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [format, setFormat] = useState('wav');
  const [quality, setQuality] = useState('medium');
  const [voice, setVoice] = useState('default');
  const [speed, setSpeed] = useState('');
  const [pitch, setPitch] = useState('');
  const [tone, setTone] = useState('');
  const [prompt, setPrompt] = useState('');
  const [username, setUsername] = useState('alice');
  const [password, setPassword] = useState('password123');
  const [userInfo, setUserInfo] = useState(null);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('info');
  const [showMsg, setShowMsg] = useState(false);
  const [catalog, setCatalog] = useState({ results: [], total: 0, page: 1, page_size: 20 });
  const [fileList, setFileList] = useState([]);
  const [batchResults, setBatchResults] = useState([]);
  const [batchProgress, setBatchProgress] = useState(0);
  const [asyncText, setAsyncText] = useState('');
  const [asyncJobs, setAsyncJobs] = useState([]); // {id, text, status, result, submittedAt}
  const pollingRef = useRef(null);
  const [catalogFilters, setCatalogFilters] = useState({ title: '', user: '', tenant: '', date: '', format: '' });
  const [selectedRows, setSelectedRows] = useState([]);
  const [editDialog, setEditDialog] = useState({ open: false, idx: null, data: {} });
  const [catalogPage, setCatalogPage] = useState(0); // zero-based for TablePagination
  const [pageSize, setPageSize] = useState(20);
  const [searchAll, setSearchAll] = useState('');
  const [batchEditDialog, setBatchEditDialog] = useState({ open: false, field: '', value: '' });
  const [jobHistory, setJobHistory] = useState({ results: [], total: 0, page: 1, page_size: 20 });
  const [jobHistoryPage, setJobHistoryPage] = useState(0);
  const [jobHistoryPageSize, setJobHistoryPageSize] = useState(20);
  const [showS3, setShowS3] = useState(false);
  const [s3Files, setS3Files] = useState([]);
  const [s3Loading, setS3Loading] = useState(false);
  const [s3NextStartAfter, setS3NextStartAfter] = useState(null);
  const [s3IsTruncated, setS3IsTruncated] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [navPage, setNavPage] = useState('home'); // 'home', 'admin', etc.
  const defaultPrefs = { language: 'en', theme: 'light', voice: 'default', speed: '', pitch: '', tone: '' };
  const [prefs, setPrefs] = useState(() => {
    try { return { ...defaultPrefs, ...JSON.parse(localStorage.getItem('prefs') || '{}') }; } catch { return defaultPrefs; }
  });
  const [showPrefs, setShowPrefs] = useState(false);
  const [notifyOnJob, setNotifyOnJob] = useState(() => {
    try { return JSON.parse(localStorage.getItem('notifyOnJob') || 'false'); } catch { return false; }
  });

  // Centralized API call with error handling
  const apiCall = async (url, options = {}) => {
    try {
      const resp = await fetch(url, options);
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Request failed');
      return data;
    } catch (e) {
      setMessage(e.message);
      setMessageType('error');
      setShowMsg(true);
      throw e;
    }
  };

  const login = async () => {
    setMessage(t('Logging in...'));
    setMessageType('info');
    setShowMsg(true);
    try {
      const data = await apiCall(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      setToken(data.token);
      // Decode JWT for user info (not secure, demo only)
      const payload = JSON.parse(atob(data.token.split('.')[1]));
      setUserInfo({ user: payload.user, tenant: payload.tenant });
      setMessage(t('Login successful!'));
      setMessageType('success');
    } catch {}
  };

  const logout = () => {
    setToken('');
    setUserInfo(null);
    setMessage(t('Logged out.'));
    setMessageType('info');
    setShowMsg(true);
  };

  const speak = async () => {
    setMessage(t('Requesting TTS...'));
    setMessageType('info');
    setShowMsg(true);
    setAudioUrl('');
    try {
      const data = await apiCall(`${API_URL}/speak`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ text, format, quality, voice, speed, pitch, tone, prompt })
      });
      setAudioUrl(data.url);
      setMessage(t('Audio generated!'));
      setMessageType('success');
    } catch {}
  };

  const fetchCatalog = async (filters = catalogFilters, pageArg = catalogPage, pageSizeArg = pageSize) => {
    setMessage(t('Fetching catalog...'));
    setMessageType('info');
    setShowMsg(true);
    let url = `${API_URL}/catalog`;
    const params = [];
    Object.entries(filters).forEach(([k, v]) => { if (v) params.push(`${k}=${encodeURIComponent(v)}`); });
    params.push(`page=${pageArg + 1}`); // backend is 1-based
    params.push(`page_size=${pageSizeArg}`);
    if (params.length) url += '?' + params.join('&');
    try {
      const data = await apiCall(url);
      setCatalog(data);
      setMessage(t('Catalog loaded.'));
      setMessageType('success');
      setShowMsg(true);
    } catch {}
  };

  // Handle filter input changes
  const handleCatalogFilter = (e) => {
    setCatalogFilters({ ...catalogFilters, [e.target.name]: e.target.value });
  };

  // Apply filters
  const applyCatalogFilters = () => {
    fetchCatalog(catalogFilters);
  };

  // Row selection for batch actions
  const handleRowSelect = (idx) => {
    setSelectedRows(rows => rows.includes(idx) ? rows.filter(i => i !== idx) : [...rows, idx]);
  };
  const handleSelectAll = (e) => {
    if (e.target.checked) setSelectedRows(catalog.results.map((_, idx) => idx));
    else setSelectedRows([]);
  };

  // Delete single or batch
  const deleteCatalogItem = async (idx) => {
    try {
      await apiCall(`${API_URL}/catalog/${idx}`, { method: 'DELETE' });
      setMessage(t('Deleted catalog item.'));
      setMessageType('success');
      setShowMsg(true);
      fetchCatalog();
    } catch {}
  };
  const deleteSelected = async () => {
    for (let idx of selectedRows) {
      await deleteCatalogItem(idx);
    }
    setSelectedRows([]);
    fetchCatalog();
  };

  // Edit metadata dialog
  const openEditDialog = (idx, row) => {
    setEditDialog({ open: true, idx, data: { ...row } });
  };
  const closeEditDialog = () => setEditDialog({ open: false, idx: null, data: {} });
  const handleEditChange = (e) => {
    setEditDialog(ed => ({ ...ed, data: { ...ed.data, [e.target.name]: e.target.value } }));
  };
  const saveEdit = async () => {
    try {
      await apiCall(`${API_URL}/catalog/${editDialog.idx}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editDialog.data)
      });
      setMessage(t('Catalog item updated.'));
      setMessageType('success');
      setShowMsg(true);
      closeEditDialog();
      fetchCatalog();
    } catch {}
  };

  // File upload handler
  const handleFileChange = (e) => {
    setFileList(Array.from(e.target.files));
    setBatchResults([]);
    setBatchProgress(0);
  };

  // Batch file upload and processing
  const processFiles = async () => {
    if (!fileList.length) return;
    setBatchResults([]);
    setBatchProgress(0);
    let results = [];
    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('format', format);
      formData.append('quality', quality);
      formData.append('voice', voice);
      formData.append('speed', speed);
      formData.append('pitch', pitch);
      formData.append('tone', tone);
      formData.append('prompt', prompt);
      try {
        const resp = await fetch(`${API_URL}/speak-file`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData
        });
        const data = await resp.json();
        if (resp.ok) {
          results.push({ file: file.name, status: 'success', url: data.url, title: data.title, duration: data.duration });
        } else {
          results.push({ file: file.name, status: 'error', error: data.error });
        }
      } catch (e) {
        results.push({ file: file.name, status: 'error', error: e.message });
      }
      setBatchProgress(Math.round(((i + 1) / fileList.length) * 100));
      setBatchResults([...results]);
    }
    setMessage(t('Batch processing complete.'));
    setMessageType('success');
    setShowMsg(true);
  };

  // Submit async TTS job
  const submitAsyncJob = async () => {
    if (!asyncText) return;
    setMessage(t('Submitting async TTS job...'));
    setMessageType('info');
    setShowMsg(true);
    try {
      const resp = await fetch(`${API_URL}/speak-async`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          text: asyncText,
          format, quality, voice, speed, pitch, tone, prompt
        })
      });
      const data = await resp.json();
      if (resp.ok && data.job_id) {
        const job = {
          id: data.job_id,
          text: asyncText,
          status: 'queued',
          result: null,
          submittedAt: new Date().toLocaleString()
        };
        setAsyncJobs(jobs => [job, ...jobs]);
        setAsyncText('');
        setMessage(t('Async job submitted!'));
        setMessageType('success');
        setShowMsg(true);
        // Start polling for this job
        pollJobStatus(data.job_id);
      } else {
        setMessage(data.error || t('Async job submission failed'));
        setMessageType('error');
        setShowMsg(true);
      }
    } catch (e) {
      setMessage(e.message);
      setMessageType('error');
      setShowMsg(true);
    }
  };

  // Poll job status
  const pollJobStatus = (jobId) => {
    const poll = async () => {
      try {
        const resp = await fetch(`${API_URL}/job/${jobId}`);
        const data = await resp.json();
        setAsyncJobs(jobs => jobs.map(j =>
          j.id === jobId ? { ...j, status: data.status, result: data.result } : j
        ));
        if (data.status === 'pending' || data.status === 'processing') {
          pollingRef.current = setTimeout(poll, 2000);
        } else if (data.status === 'complete') {
          notifyJobComplete(data);
        }
        if (data.status === 'complete' && notifyOnJob && window.Notification && Notification.permission === 'granted') {
          notifyJobComplete({ ...job, ...data });
        }
      } catch {}
    };
    poll();
  };

  // Optionally, poll all jobs that are not complete/error on mount
  React.useEffect(() => {
    asyncJobs.forEach(job => {
      if (job.status === 'pending' || job.status === 'processing') {
        pollJobStatus(job.id);
      }
    });
    return () => { if (pollingRef.current) clearTimeout(pollingRef.current); };
    // eslint-disable-next-line
  }, []);

  // Pagination handlers
  const handleChangePage = (event, newPage) => {
    setCatalogPage(newPage);
    fetchCatalog(catalogFilters, newPage, pageSize);
  };
  const handleChangeRowsPerPage = (event) => {
    const newSize = parseInt(event.target.value, 10);
    setPageSize(newSize);
    setCatalogPage(0);
    fetchCatalog(catalogFilters, 0, newSize);
  };

  // CSV export
  const handleExportCSV = () => {
    let url = `${API_URL}/catalog?export=csv`;
    const params = [];
    Object.entries(catalogFilters).forEach(([k, v]) => { if (v) params.push(`${k}=${encodeURIComponent(v)}`); });
    if (params.length) url += '&' + params.join('&');
    window.open(url, '_blank');
  };

  // Advanced search: filter client-side for searchAll
  const filteredResults = searchAll
    ? catalog.results.filter(row =>
        Object.values(row).some(val =>
          val && val.toString().toLowerCase().includes(searchAll.toLowerCase())
        )
      )
    : catalog.results;

  // Batch actions
  const handleBatchDownload = async () => {
    if (!selectedRows.length) return;
    const indices = selectedRows;
    const resp = await fetch(`${API_URL}/catalog/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'download', indices })
    });
    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'catalog_batch.zip';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleBatchExportCSV = async () => {
    if (!selectedRows.length) return;
    const indices = selectedRows;
    const resp = await fetch(`${API_URL}/catalog/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'export_csv', indices })
    });
    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'catalog_batch.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const openBatchEditDialog = () => setBatchEditDialog({ open: true, field: '', value: '' });
  const closeBatchEditDialog = () => setBatchEditDialog({ open: false, field: '', value: '' });
  const handleBatchEditField = (e) => setBatchEditDialog(d => ({ ...d, field: e.target.value }));
  const handleBatchEditValue = (e) => setBatchEditDialog(d => ({ ...d, value: e.target.value }));
  const saveBatchEdit = async () => {
    if (!batchEditDialog.field) return;
    await fetch(`${API_URL}/catalog/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'edit', indices: selectedRows, update: { [batchEditDialog.field]: batchEditDialog.value } })
    });
    setMessage(t('Batch edit complete.'));
    setMessageType('success');
    setShowMsg(true);
    closeBatchEditDialog();
    fetchCatalog();
  };

  const resetFilters = () => {
    setCatalogFilters({ title: '', user: '', tenant: '', date: '', format: '' });
    setSearchAll('');
    fetchCatalog({ title: '', user: '', tenant: '', date: '', format: '' });
  };

  // Fetch persistent job history
  const fetchJobHistory = async (pageArg = jobHistoryPage, pageSizeArg = jobHistoryPageSize) => {
    let url = `${API_URL}/jobs?page=${pageArg + 1}&page_size=${pageSizeArg}`;
    if (userInfo && userInfo.user) url += `&user=${encodeURIComponent(userInfo.user)}`;
    try {
      const data = await apiCall(url);
      setJobHistory(data);
    } catch {}
  };

  // On mount and when userInfo changes, fetch job history
  useEffect(() => {
    if (token && userInfo) fetchJobHistory(0, jobHistoryPageSize);
    // eslint-disable-next-line
  }, [token, userInfo]);

  // Pagination handlers for job history
  const handleJobHistoryPage = (event, newPage) => {
    setJobHistoryPage(newPage);
    fetchJobHistory(newPage, jobHistoryPageSize);
  };
  const handleJobHistoryRowsPerPage = (event) => {
    const newSize = parseInt(event.target.value, 10);
    setJobHistoryPageSize(newSize);
    setJobHistoryPage(0);
    fetchJobHistory(0, newSize);
  };

  // On mount, fetch first page
  useEffect(() => {
    fetchCatalog(catalogFilters, 0, pageSize);
    // eslint-disable-next-line
  }, []);

  // S3 file management
  const fetchS3Files = async (startAfter = '') => {
    setS3Loading(true);
    let url = `${API_URL}/s3/list?max_keys=100`;
    if (startAfter) url += `&start_after=${encodeURIComponent(startAfter)}`;
    try {
      const resp = await fetch(url);
      const data = await resp.json();
      if (resp.ok) {
        setS3Files(startAfter ? [...s3Files, ...data.files] : data.files);
        setS3NextStartAfter(data.next_start_after);
        setS3IsTruncated(data.is_truncated);
      } else {
        setMessage(data.error || t('Failed to list S3 files'));
        setMessageType('error');
        setShowMsg(true);
      }
    } catch (e) {
      setMessage(e.message);
      setMessageType('error');
      setShowMsg(true);
    }
    setS3Loading(false);
  };
  const handleS3Download = (key) => {
    window.open(`${API_URL}/s3/download?key=${encodeURIComponent(key)}`, '_blank');
  };
  const handleS3Delete = async (key) => {
    if (!window.confirm(t('Delete this file from S3?'))) return;
    try {
      const resp = await fetch(`${API_URL}/s3/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key })
      });
      const data = await resp.json();
      if (resp.ok) {
        setMessage(t('File deleted from S3'));
        setMessageType('success');
        setShowMsg(true);
        setS3Files(files => files.filter(f => f.key !== key));
      } else {
        setMessage(data.error || t('Failed to delete S3 file'));
        setMessageType('error');
        setShowMsg(true);
      }
    } catch (e) {
      setMessage(e.message);
      setMessageType('error');
      setShowMsg(true);
    }
  };

  // S3 tab toggle
  const handleShowS3 = () => {
    setShowS3(true);
    fetchS3Files();
  };

  useEffect(() => {
    // Check if user is admin (assume JWT payload has 'role')
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setIsAdmin(payload.role === 'admin');
      } catch (e) {
        setIsAdmin(false);
      }
    } else {
      setIsAdmin(false);
    }
  }, []);

  // On mount, apply language/theme from prefs
  useEffect(() => {
    if (prefs.language) i18n.changeLanguage(prefs.language);
    // Theme handled below
  }, []);

  // Save preferences
  const handleSavePrefs = (newPrefs) => {
    setPrefs(newPrefs);
    localStorage.setItem('prefs', JSON.stringify(newPrefs));
    if (newPrefs.language) i18n.changeLanguage(newPrefs.language);
  };

  // Notification permission request
  useEffect(() => {
    if (notifyOnJob && 'Notification' in window && Notification.permission !== 'granted') {
      Notification.requestPermission();
    }
  }, [notifyOnJob]);

  // Notify job completion
  const notifyJobComplete = (job) => {
    if (notifyOnJob && window.Notification && Notification.permission === 'granted') {
      new Notification(t('Job complete'), { body: t('Your async TTS job has finished.') });
    }
  };

  return (
    <Container maxWidth="md">
      <AppBar position="static" color="primary" role="banner">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }} id="main-title">{t('DiaSpeak Web UI')}</Typography>
          <LanguageSwitcher />
          <Button color="inherit" startIcon={<CloudQueueIcon />} onClick={handleShowS3} sx={{ ml: 2 }} aria-label={t('Cloud Files')} tabIndex={0}>{t('Cloud Files')}</Button>
          {isAdmin && (
            <Button color="inherit" onClick={() => setNavPage('admin')} sx={{ ml: 2 }} aria-label={t('Admin Panel')} tabIndex={0}>{t('Admin Panel')}</Button>
          )}
          {userInfo && (
            <>
              <Typography variant="body2" sx={{ mr: 2 }} aria-label={t('User')}>{userInfo.user} ({userInfo.tenant})</Typography>
              <IconButton color="inherit" onClick={logout} aria-label={t('Logout')} tabIndex={0}><LogoutIcon /></IconButton>
            </>
          )}
          <Button color="inherit" onClick={() => setShowPrefs(true)} sx={{ ml: 2 }} aria-label={t('Preferences')} tabIndex={0}>{t('Preferences')}</Button>
        </Toolbar>
      </AppBar>
      <nav>
        {/* ...existing nav items... */}
        {isAdmin && (
          <button aria-label={t('Admin Panel')} onClick={() => setNavPage('admin')}>{t('Admin Panel')}</button>
        )}
      </nav>
      {showS3 ? (
        <Box mt={4}>
          <Typography variant="h6" sx={{ mb: 2 }} id="cloud-files-title"><CloudQueueIcon sx={{ mr: 1 }} />{t('Cloud Files')} (S3)</Typography>
          <Button variant="outlined" onClick={() => { setShowS3(false); }} aria-label={t('Back')} tabIndex={0}>{t('Back')}</Button>
          <TableContainer component={Paper} sx={{ mt: 2 }} role="table" aria-label={t('Cloud Files')}>
            <Table size="small" aria-labelledby="cloud-files-title">
              <TableHead>
                <TableRow>
                  <TableCell>{t('Key')}</TableCell>
                  <TableCell>{t('Size')}</TableCell>
                  <TableCell>{t('Last Modified')}</TableCell>
                  <TableCell>{t('Actions')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {s3Files.map((file, idx) => (
                  <TableRow key={file.key} tabIndex={0} aria-label={file.key}>
                    <TableCell sx={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file.key}</TableCell>
                    <TableCell>{file.size}</TableCell>
                    <TableCell>{file.last_modified}</TableCell>
                    <TableCell>
                      <Button size="small" onClick={() => handleS3Download(file.key)} aria-label={t('Download')} tabIndex={0}>{t('Download')}</Button>
                      <IconButton color="error" onClick={() => handleS3Delete(file.key)} aria-label={t('Delete')} tabIndex={0}><DeleteForeverIcon /></IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          {s3IsTruncated && (
            <Button variant="contained" onClick={() => fetchS3Files(s3NextStartAfter)} disabled={s3Loading} sx={{ mt: 2 }} aria-label={t('Load More')} tabIndex={0}>{t('Load More')}</Button>
          )}
        </Box>
      ) : (
        <Box mt={4}>
          {!token ? (
            <Box className="login-box" sx={{ mb: 4 }}>
              <Typography variant="h6">{t('Login')}</Typography>
              <TextField label={t('Username')} value={username} onChange={e => setUsername(e.target.value)} fullWidth sx={{ mb: 2 }} />
              <TextField label={t('Password')} value={password} onChange={e => setPassword(e.target.value)} type="password" fullWidth sx={{ mb: 2 }} />
              <Button variant="contained" onClick={login}>{t('Login')}</Button>
            </Box>
          ) : (
            <Box className="tts-box" sx={{ mb: 4 }}>
              <Typography variant="h6">{t('Text-to-Speech')}</Typography>
              <TextField
                label={t('Text to Synthesize')}
                value={text}
                onChange={e => setText(e.target.value)}
                multiline rows={4} fullWidth sx={{ mb: 2 }}
              />
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={4}>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>{t('Format')}</InputLabel>
                    <Select value={format} label={t('Format')} onChange={e => setFormat(e.target.value)}>
                      <MenuItem value="wav">WAV</MenuItem>
                      <MenuItem value="mp3">MP3</MenuItem>
                      <MenuItem value="ogg">OGG</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>{t('Quality')}</InputLabel>
                    <Select value={quality} label={t('Quality')} onChange={e => setQuality(e.target.value)}>
                      <MenuItem value="low">Low</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="high">High</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <TextField label={t('Voice')} value={voice} onChange={e => setVoice(e.target.value)} fullWidth sx={{ mb: 2 }} />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <TextField label={t('Speed')} value={speed} onChange={e => setSpeed(e.target.value)} fullWidth sx={{ mb: 2 }} />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <TextField label={t('Pitch')} value={pitch} onChange={e => setPitch(e.target.value)} fullWidth sx={{ mb: 2 }} />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <TextField label={t('Tone')} value={tone} onChange={e => setTone(e.target.value)} fullWidth sx={{ mb: 2 }} />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <TextField label={t('Prompt')} value={prompt} onChange={e => setPrompt(e.target.value)} fullWidth sx={{ mb: 2 }} />
                </Grid>
              </Grid>
              <Button variant="contained" onClick={speak} disabled={!token || !text}>{t('Speak')}</Button>
              {audioUrl && (
                <Box mt={2}>
                  <AudioPlayer src={audioUrl} />
                  <Button href={audioUrl} download sx={{ mt: 1 }}>{t('Download Audio')}</Button>
                </Box>
              )}
            </Box>
          )}
          {token && (
            <Box className="file-upload-box" sx={{ mb: 4 }}>
              <Typography variant="h6">{t('File Upload & Batch Processing')}</Typography>
              <input
                type="file"
                multiple
                accept=".txt,.md,.json"
                onChange={handleFileChange}
                style={{ marginBottom: 16 }}
              />
              <Button variant="contained" onClick={processFiles} disabled={!fileList.length} sx={{ ml: 2 }}>
                {t('Process Files')}
              </Button>
              {batchProgress > 0 && batchProgress < 100 && (
                <Box sx={{ width: '100%', mt: 2 }}>
                  <LinearProgress variant="determinate" value={batchProgress} />
                  <Typography variant="body2">{batchProgress}%</Typography>
                </Box>
              )}
              {batchResults.length > 0 && (
                <List sx={{ mt: 2 }}>
                  {batchResults.map((res, idx) => (
                    <ListItem key={idx} divider>
                      <ListItemText
                        primary={res.file + (res.title ? ` (${res.title})` : '')}
                        secondary={res.status === 'success' ? (
                          <span>
                            {t('Success')} - <a href={res.url} target="_blank" rel="noopener noreferrer">{t('Play')}</a> {res.duration && `- ${res.duration}`}
                          </span>
                        ) : (
                          <span style={{ color: 'red' }}>{t('Error')}: {res.error}</span>
                        )}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          )}
          {token && (
            <Box className="async-job-box" sx={{ mb: 4 }}>
              <Typography variant="h6">{t('Async TTS Job Dashboard')}</Typography>
              <TextField
                label={t('Text for Async TTS')}
                value={asyncText}
                onChange={e => setAsyncText(e.target.value)}
                multiline rows={2} fullWidth sx={{ mb: 2 }}
              />
              <Button variant="contained" onClick={submitAsyncJob} disabled={!asyncText} sx={{ mb: 2 }}>
                {t('Submit Async Job')}
              </Button>
              <TableContainer component={Paper} sx={{ mt: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('Job ID')}</TableCell>
                      <TableCell>{t('Text')}</TableCell>
                      <TableCell>{t('Status')}</TableCell>
                      <TableCell>{t('Submitted')}</TableCell>
                      <TableCell>{t('Result')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {asyncJobs.map((job, idx) => (
                      <TableRow key={job.id}>
                        <TableCell>{job.id}</TableCell>
                        <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{job.text}</TableCell>
                        <TableCell>
                          <Chip label={job.status} color={
                            job.status === 'complete' ? 'success' :
                            job.status === 'error' ? 'error' :
                            job.status === 'processing' ? 'warning' : 'default'
                          } />
                        </TableCell>
                        <TableCell>{job.submittedAt}</TableCell>
                        <TableCell>
                          {job.status === 'complete' && job.result && job.result.url && (
                            <AudioPlayer src={job.result.url} />
                          )}
                          {job.status === 'error' && job.result && (
                            <span style={{ color: 'red' }}>{job.result.message || t('Error')}</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              {/* Persistent Job History Table */}
              <Box sx={{ mt: 4 }}>
                <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', mb: 1 }}><HistoryIcon sx={{ mr: 1 }} />{t('Job History')}</Typography>
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>{t('Job ID')}</TableCell>
                        <TableCell>{t('Text')}</TableCell>
                        <TableCell>{t('Status')}</TableCell>
                        <TableCell>{t('Submitted')}</TableCell>
                        <TableCell>{t('Completed')}</TableCell>
                        <TableCell>{t('Result')}</TableCell>
                        <TableCell>{t('Error')}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {jobHistory.results.map((job, idx) => (
                        <TableRow key={job.job_id}>
                          <TableCell>{job.job_id}</TableCell>
                          <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{job.text}</TableCell>
                          <TableCell>
                            <Chip label={job.status} color={
                              job.status === 'complete' ? 'success' :
                              job.status === 'error' ? 'error' :
                              job.status === 'processing' ? 'warning' : 'default'
                            } />
                          </TableCell>
                          <TableCell>{job.submitted_at}</TableCell>
                          <TableCell>{job.completed_at}</TableCell>
                          <TableCell>
                            {job.result_url ? <a href={job.result_url} target="_blank" rel="noopener noreferrer">{t('Audio')}</a> : ''}
                          </TableCell>
                          <TableCell sx={{ color: 'red' }}>{job.error}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <TablePagination
                    component="div"
                    count={jobHistory.total}
                    page={jobHistoryPage}
                    onPageChange={handleJobHistoryPage}
                    rowsPerPage={jobHistoryPageSize}
                    onRowsPerPageChange={handleJobHistoryRowsPerPage}
                    rowsPerPageOptions={[10, 20, 50, 100]}
                  />
                </TableContainer>
              </Box>
            </Box>
          )}
          <Box className="catalog-box" sx={{ mb: 4 }}>
            <Typography variant="h6">{t('Catalog')}</Typography>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6} md={2}><TextField label={t('Title')} name="title" value={catalogFilters.title} onChange={handleCatalogFilter} size="small" fullWidth /></Grid>
              <Grid item xs={12} sm={6} md={2}><TextField label={t('User')} name="user" value={catalogFilters.user} onChange={handleCatalogFilter} size="small" fullWidth /></Grid>
              <Grid item xs={12} sm={6} md={2}><TextField label={t('Tenant')} name="tenant" value={catalogFilters.tenant} onChange={handleCatalogFilter} size="small" fullWidth /></Grid>
              <Grid item xs={12} sm={6} md={2}><TextField label={t('Date')} name="date" value={catalogFilters.date} onChange={handleCatalogFilter} size="small" fullWidth placeholder="YYYY-MM-DD" /></Grid>
              <Grid item xs={12} sm={6} md={2}><TextField label={t('Format')} name="format" value={catalogFilters.format} onChange={handleCatalogFilter} size="small" fullWidth /></Grid>
              <Grid item xs={12} sm={6} md={2}><Button variant="outlined" onClick={applyCatalogFilters}>{t('Filter')}</Button></Grid>
              <Grid item xs={12} sm={6} md={2}><Button variant="outlined" onClick={resetFilters}>{t('Reset')}</Button></Grid>
              <Grid item xs={12} sm={6} md={3}><TextField label={t('Search All')} value={searchAll} onChange={e => setSearchAll(e.target.value)} size="small" fullWidth /></Grid>
              <Grid item xs={12} sm={6} md={2}><Button variant="outlined" startIcon={<GetAppIcon />} onClick={handleExportCSV}>{t('Export CSV')}</Button></Grid>
              <Grid item xs={12} sm={6} md={2}><Button variant="outlined" startIcon={<CloudDownloadIcon />} onClick={handleBatchDownload} disabled={!selectedRows.length}>{t('Batch Download')}</Button></Grid>
              <Grid item xs={12} sm={6} md={2}><Button variant="outlined" startIcon={<GetAppIcon />} onClick={handleBatchExportCSV} disabled={!selectedRows.length}>{t('Batch Export')}</Button></Grid>
              <Grid item xs={12} sm={6} md={2}><Button variant="outlined" startIcon={<EditIcon />} onClick={openBatchEditDialog} disabled={!selectedRows.length}>{t('Batch Edit')}</Button></Grid>
            </Grid>
            <Button variant="contained" color="error" onClick={deleteSelected} disabled={!selectedRows.length} sx={{ mb: 1 }} startIcon={<DeleteIcon />}>{t('Delete Selected')}</Button>
            <TableContainer component={Paper} sx={{ mt: 1 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox"><Checkbox checked={selectedRows.length === catalog.results.length && catalog.results.length > 0} indeterminate={selectedRows.length > 0 && selectedRows.length < catalog.results.length} onChange={handleSelectAll} /></TableCell>
                    <TableCell>{t('Title')}</TableCell>
                    <TableCell>{t('Date')}</TableCell>
                    <TableCell>{t('Length')}</TableCell>
                    <TableCell>{t('Format')}</TableCell>
                    <TableCell>{t('Quality')}</TableCell>
                    <TableCell>{t('User')}</TableCell>
                    <TableCell>{t('Tenant')}</TableCell>
                    <TableCell>{t('S3')}</TableCell>
                    <TableCell>{t('Actions')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredResults.map((row, idx) => (
                    <TableRow key={idx} selected={selectedRows.includes(idx)}>
                      <TableCell padding="checkbox"><Checkbox checked={selectedRows.includes(idx)} onChange={() => handleRowSelect(idx)} /></TableCell>
                      <TableCell>{row.title || <i>({t('untitled')})</i>}</TableCell>
                      <TableCell>{row.date}</TableCell>
                      <TableCell>{row.length}</TableCell>
                      <TableCell>{row.format}</TableCell>
                      <TableCell>{row.quality}</TableCell>
                      <TableCell>{row.user}</TableCell>
                      <TableCell>{row.tenant}</TableCell>
                      <TableCell>{row.s3_url ? <a href={row.s3_url} target="_blank" rel="noopener noreferrer">{t('S3')}</a> : ''}</TableCell>
                      <TableCell>
                        {row.url || row.file_path ? <AudioPlayer src={row.url || row.file_path} /> : null}
                        {row.url || row.file_path ? <IconButton href={row.url || row.file_path} download><DownloadIcon /></IconButton> : null}
                        <IconButton onClick={() => openEditDialog(idx, row)}><EditIcon /></IconButton>
                        <IconButton color="error" onClick={() => deleteCatalogItem(idx)}><DeleteIcon /></IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <TablePagination
                component="div"
                count={catalog.total}
                page={catalogPage}
                onPageChange={handleChangePage}
                rowsPerPage={pageSize}
                onRowsPerPageChange={handleChangeRowsPerPage}
                rowsPerPageOptions={[10, 20, 50, 100]}
              />
            </TableContainer>
            {/* Batch Edit Dialog */}
            <Dialog open={batchEditDialog.open} onClose={closeBatchEditDialog}>
              <DialogTitle>{t('Batch Edit Catalog Field')}</DialogTitle>
              <DialogContent>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>{t('Field')}</InputLabel>
                  <Select value={batchEditDialog.field} label={t('Field')} onChange={handleBatchEditField}>
                    {['title','tone','prompt','voice','speed','pitch','format','quality'].map(field => (
                      <MenuItem key={field} value={field}>{t(field.charAt(0).toUpperCase()+field.slice(1))}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <TextField label={t('Value')} value={batchEditDialog.value} onChange={handleBatchEditValue} fullWidth />
              </DialogContent>
              <DialogActions>
                <Button onClick={closeBatchEditDialog}>{t('Cancel')}</Button>
                <Button onClick={saveBatchEdit} variant="contained" startIcon={<SaveIcon />}>{t('Save')}</Button>
              </DialogActions>
            </Dialog>
            {/* Edit Metadata Dialog */}
            <Dialog open={editDialog.open} onClose={closeEditDialog}>
              <DialogTitle>{t('Edit Catalog Metadata')}</DialogTitle>
              <DialogContent>
                {['title','tone','prompt','voice','speed','pitch','format','quality'].map(field => (
                  <TextField key={field} label={t(field.charAt(0).toUpperCase()+field.slice(1))} name={field} value={editDialog.data[field]||''} onChange={handleEditChange} fullWidth sx={{ mb: 2 }} />
                ))}
              </DialogContent>
              <DialogActions>
                <Button onClick={closeEditDialog}>{t('Cancel')}</Button>
                <Button onClick={saveEdit} variant="contained">{t('Save')}</Button>
              </DialogActions>
            </Dialog>
          </Box>
        </Box>
      )}
      {navPage === 'admin' && isAdmin && <AdminPanel />}
      <PreferencesDialog open={showPrefs} onClose={() => setShowPrefs(false)} onSave={handleSavePrefs} prefs={prefs} />
      <Snackbar open={showMsg} autoHideDuration={4000} onClose={() => setShowMsg(false)}>
        <Alert onClose={() => setShowMsg(false)} severity={messageType} sx={{ width: '100%' }}>
          {message}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default App;
