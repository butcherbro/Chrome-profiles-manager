import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window
import "./components"

ApplicationWindow {
    id: window
    visible: true
    width: 400
    height: 600
    title: "Chrome Profile Manager"
    color: "#f0f0f0"  // Светло-серый фон

    // Добавляем обработчик закрытия окна
    onClosing: function(close) {
        // Вызываем функцию корректного завершения работы приложения
        profileManager.quit_application()
        // Принимаем событие закрытия
        close.accepted = false  // Изменяем на false, чтобы контролировать закрытие через quit_application
    }
    
    // Обработчик сигнала о блокировке закрытия приложения
    Connections {
        target: profileManager
        
        function onApplicationCloseBlockedChanged(message) {
            // Показываем уведомление пользователю
            notificationPopup.text = message
            notificationPopup.open()
        }
        
        function onConfirmApplicationCloseRequested(message) {
            // Показываем диалог подтверждения закрытия
            confirmCloseDialog.text = message
            confirmCloseDialog.open()
        }
    }
    
    // Всплывающее уведомление
    Popup {
        id: notificationPopup
        width: parent.width * 0.8
        height: notificationText.height + 80  // Увеличиваем высоту для двух кнопок
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        
        property string text: ""
        
        contentItem: ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10
            
            Text {
                id: notificationText
                text: notificationPopup.text
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }
            
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 10
                
                Button {
                    text: "OK"
                    onClicked: notificationPopup.close()
                }
                
                Button {
                    text: "Принудительно закрыть"
                    onClicked: {
                        notificationPopup.close()
                        profileManager.force_quit_application()
                    }
                }
            }
        }
    }

    // Диалог подтверждения закрытия приложения
    Popup {
        id: confirmCloseDialog
        width: parent.width * 0.8
        height: confirmCloseText.height + 80
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        
        property string text: ""
        
        contentItem: ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10
            
            Text {
                id: confirmCloseText
                text: confirmCloseDialog.text
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }
            
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 10
                
                Button {
                    text: "Отмена"
                    onClicked: confirmCloseDialog.close()
                }
                
                Button {
                    text: "Закрыть приложение"
                    onClicked: {
                        confirmCloseDialog.close()
                        profileManager.confirmed_quit_application()
                    }
                }
            }
        }
    }

    // Создаем экземпляры компонентов
    ExtensionManager {
        id: extensionManagerWindow
        visible: false
        
        onBackClicked: {
            // Обновляем список профилей при закрытии окна управления расширениями
            profileManager.update_profiles_list()
        }
    }
    
    ChromeScriptsRunner {
        id: chromeScriptsRunner
        visible: false
        
        onBackClicked: {
            // Обновляем список профилей при закрытии окна прогона скриптов
            profileManager.update_profiles_list()
        }
    }
    
    ManagerScriptsRunner {
        id: managerScriptsRunner
        visible: false
        
        onBackClicked: {
            // Обновляем список профилей при закрытии окна прогона скриптов
            profileManager.update_profiles_list()
        }
    }
    
    ProfileListManager {
        id: profileListManagerWindow
        visible: false
        
        onBackClicked: {
            // Обновляем список профилей при закрытии окна управления профилями и списками
            profileManager.update_profiles_list()
        }
    }
    
    ProfileLauncher {
        id: profileLauncherWindow
        visible: false
        
        onBackClicked: {
            // Обновляем список профилей при закрытии окна запуска профилей
            profileManager.update_profiles_list()
        }
    }

    Component.onCompleted: {
        profileManager.update_profiles_list()
    }

    StackView {
        id: stackView
        objectName: "stackView"
        anchors.fill: parent
        initialItem: mainMenu
    }

    // Главное меню
    Component {
        id: mainMenu
        
        Rectangle {
            color: "#f0f0f0"
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                Text {
                    text: "Chrome Profile Manager"
                    font.pixelSize: 20
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                    Layout.bottomMargin: 20
                }

                // Кнопки меню
                Repeater {
                    model: [
                        { text: "Запустить профили", icon: "🚀", action: function() { profileLauncherWindow.show() } },
                        { text: "Просмотр профилей", icon: "📖", action: function() { stackView.push(profileViewer) } },
                        { text: "Обновить комментарии", icon: "📝", action: function() { stackView.push(profileCommentEditor) } },
                        { text: "Управление расширениями", icon: "🧩", action: function() { extensionManagerWindow.show() } },
                        { text: "Прогон скриптов [chrome]", icon: "🤖", action: function() { chromeScriptsRunner.show() } },
                        { text: "Прогон скриптов [manager]", icon: "🤖", action: function() { managerScriptsRunner.show() } },
                        { text: "Создание профилей и списков", icon: "➕", action: function() { profileListManagerWindow.show() } },
                        { text: "Убить процессы Chrome", icon: "💀", action: function() { profileManager.kill_chrome() } },
                        { text: "Выход", icon: "🚪", action: function() { profileManager.quit_application() } }
                    ]

                    delegate: Button {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 50
                        flat: true

                        background: Rectangle {
                            color: parent.hovered ? "#e0e0e0" : "#ffffff"
                            radius: 4
                        }

                        contentItem: RowLayout {
                            spacing: 10
                            
                            Text {
                                text: modelData.icon
                                font.pixelSize: 24
                                Layout.preferredWidth: 30
                                horizontalAlignment: Text.AlignHCenter
                            }
                            
                            Text {
                                text: modelData.text
                                Layout.fillWidth: true
                                horizontalAlignment: Text.AlignLeft
                            }
                        }

                        onClicked: modelData.action()
                    }
                }

                // Растягивающийся элемент для заполнения пространства
                Item {
                    Layout.fillHeight: true
                }
            }
        }
    }

    // Подменю выбора профилей
    Component {
        id: profileSelectionMenu
        
        ProfileSelectionMenu {
            onBackClicked: stackView.pop()
        }
    }

    // Компонент списка профилей
    Component {
        id: profileListSelection
        
        ProfileListSelection {
            onBackClicked: stackView.pop()
        }
    }

    // Компонент ввода названий
    Component {
        id: profileNameEntry
        
        ProfileNameEntry {
            onBackClicked: stackView.pop()
        }
    }

    // Компонент выбора по комментарию
    Component {
        id: profileCommentSelection
        
        ProfileCommentSelection {
            onBackClicked: stackView.pop()
        }
    }
    
    // Компонент редактирования комментариев
    Component {
        id: profileCommentEditor
        
        ProfileCommentEditor {
            onBackClicked: stackView.pop()
        }
    }
    
    // Компонент просмотра профилей
    Component {
        id: profileViewer
        
        ProfileViewer {
            onBackClicked: stackView.pop()
        }
    }

    // Компонент создания профиля
    Component {
        id: profileCreator
        
        ProfileCreator {
            onBackClicked: stackView.pop()
        }
    }
    
    // Компонент списка расширений
    Component {
        id: extensionsList
        
        ExtensionsList {
            onBackClicked: stackView.pop()
        }
    }
} 