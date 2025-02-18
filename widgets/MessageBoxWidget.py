"""

This module contains the MessageBoxWidget class, which serves as a container
for MessageWidget instances in a chat application.

Classes:
    - MessageBoxWidget: A QWidget subclass that holds and manages multiple MessageWidgets.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStyle, QStyleOption, QSizePolicy, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter
from . import MessageWidget
from ConversationNode import ConversationNode
from ChatGPT import response, dummyResponse
class MessageBoxWidget(QWidget):
    """A container widget for multiple MessageWidgets.

    This class serves as the vertical container for MessageWidgets to display messages
    in a chat application.

    Methods:
        - addMessage: Adds a new MessageWidget with the given message.
        - popMessage: Removes and returns the oldest MessageWidget.
    """
    changed_signal = pyqtSignal(ConversationNode, ConversationNode)
    
    def __init__(self, *args, **kwargs):
        """Initialize the MessageBoxWidget."""
        super().__init__(*args, **kwargs)
        self._initConv()
        self._initUI()

    def _initConv(self):
        root_message_widget = MessageWidget("")
        root_node = ConversationNode("Nothing goes here.", "root")
        root_message_widget.node = root_node

        self.message_widgets = [root_message_widget]
        self.current_message = root_message_widget
        
    def _initUI(self):
        """Initialize the user interface components."""
        self._setupLayout()
        self.inner_widget = QWidget()
        self.inner_widget.setLayout(self.layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.inner_widget)
        self.scroll_area.verticalScrollBar().rangeChanged.connect(self._scrollToBottom)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll_area)

        self._setupStyleSheet()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
                
    def _setupLayout(self):
        """Setup the QVBoxLayout to house MessageWidgets."""
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.layout)

    def _setupStyleSheet(self):
        """Setup the stylesheet for this widget."""
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            MessageBoxWidget {
                background-color: rgba(0, 0, 0, 0.1);
            }
            QScrollArea {
                # border: none;
                background-color: rgba(0, 0, 0, 0.1);
            }
            QWidget {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)

    
    def _markChange(self):
        chatbox = self.parent()
        central_widget = chatbox.parent()
        main_window = central_widget.parent()
        main_window.changed = True
        main_window.update_title()
        self.changed_signal.emit(self.root(), self.current_message.node)
    def _setCurrentMessage(self, curr):
        print("Called.")
        self.current_message = curr
        self._populate(self.root(), curr)
    def root(self):
        return self.message_widgets[0].node
    def addMessage(self, message, node=None, robot=False, load=False):
        """Add a new MessageWidget with the given message."""
        message_widget = MessageWidget(message, robot=robot)
        if node is None:
            if robot:
                user = "assistant"
            else:
                user = "user"
            node = ConversationNode(message, user=user)
        message_widget.defineNode(node)

        #connect the nodes
        if self.current_message and node is not None:
            parent_node = self.current_message.node
            child_node = message_widget.node
            parent_node.add(child_node)

        self.message_widgets.append(message_widget)
        self.layout.addWidget(message_widget)
        self.current_message = message_widget

        #print the root node
        root_node = self.message_widgets[0].node
        print(root_node)



        if not robot and not load:

            messages = self.current_message.node.return_conversation()
            messages = messages[1:]
            #update syntax
            messages = [{'role':usr, 'content':msg} for usr,msg in messages]
            print(messages)
            resp = response(messages)
            self.addMessage(message = resp, robot=True)

        self._markChange()
        
    def _scrollToBottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def _populate(self, root, curr):
        """Populate the MessageBoxWidget with the given conversation nodes."""
        self.deleteConversation()
        self._initConv()
        self.message_widgets[0].node = root
        conversation = []
        def __append_conversation(node):
            if node.parent:
                __append_conversation(node.parent)
            if node:
                conversation.append(node)
        __append_conversation(curr)

        #update the root node
        root_node = conversation[0]
        self.message_widgets[0].node = root_node
        conversation = conversation[1:]
        for node in conversation:
            robot = node.user == 'assistant'
            self.addMessage(message=node.text, node=node, load=True, robot=robot)




    def deleteConversation(self):
        while len(self.message_widgets) > 1:
            self.popMessage()
        root_node = self.message_widgets[0].node
        root_node.delete()

    def popMessage(self):
        """Remove and return the oldest MessageWidget."""
        if len(self.message_widgets) > 1:
            message_widget = self.message_widgets.pop()
            self.layout.removeWidget(message_widget)
            message_widget.deleteLater()

            #update self.current_message
            self.current_message = self.message_widgets[-1] if self.message_widgets else None

            self._markChange()
            return message_widget

    def paintEvent(self, e):
        """Ensure the custom stylesheet works properly."""
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, option, painter, self)
